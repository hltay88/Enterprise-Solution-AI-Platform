"""Sprint 5.2 — hybrid retrieval (vector + keyword) with citations."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.constants.knowledge_lifecycle import RETRIEVAL_ELIGIBLE_STATUSES
from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.models.knowledge import RetrievalResult, RetrievalRun
from app.models.user import User
from app.schemas.retrieval import (
    CitationOut,
    RetrievalContextOut,
    RetrievalHitOut,
    RetrievalSearchIn,
    RetrievalSearchOut,
)

from app.services.rerank import rerank_hits


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedder = get_embedding_provider()

    def search(self, body: RetrievalSearchIn, user: User) -> RetrievalSearchOut:
        query = (body.query or "").strip()
        if not query:
            raise ValidationAppError("query is required")

        top_k = int(body.top_k or settings.atlas_retrieval_top_k or 8)
        top_k = max(1, min(top_k, 50))
        started = time.perf_counter()

        query_vec = self.embedder.embed_query(query)
        tenant_id = getattr(user, "active_tenant_id", None)
        vec_hits = self._vector_search(query_vec, body, limit=top_k * 3, tenant_id=tenant_id)
        kw_hits = self._keyword_search(query, body, limit=top_k * 3, tenant_id=tenant_id)
        fused = self._rrf_fuse(vec_hits, kw_hits, top_k=top_k * 2)
        reranked = rerank_hits(query, fused, top_k=top_k)

        min_score = float(
            body.min_score if body.min_score is not None else settings.atlas_retrieval_min_score,
        )
        hits = [h for h in reranked if (h.get("fused_score") or 0) >= min_score]
        if body.max_per_item:
            hits = self._diversify(hits, max_per_item=body.max_per_item)

        insufficient = len(hits) == 0
        latency_ms = int((time.perf_counter() - started) * 1000)

        run = RetrievalRun(
            tenant_id=getattr(user, "active_tenant_id", None),
            user_id=user.id,
            query_text=query,
            filters_json={
                "domain_code": body.domain_code,
                "knowledge_type": body.knowledge_type,
                "project_id": str(body.project_id) if body.project_id else None,
            },
            top_k=top_k,
            embedding_provider=self.embedder.name,
            embedding_model=self.embedder.model,
            latency_ms=latency_ms,
            result_count=len(hits),
            insufficient_evidence=insufficient,
            metadata_json={
                "min_score": min_score,
                "reranker": "local_lexical_rrf",
                "candidate_count": len(fused),
            },
        )
        self.db.add(run)
        self.db.flush()

        out_hits: list[RetrievalHitOut] = []
        for rank, hit in enumerate(hits, start=1):
            citation = self._citation_from_hit(hit)
            self.db.add(
                RetrievalResult(
                    retrieval_run_id=run.id,
                    knowledge_chunk_id=hit["chunk_id"],
                    knowledge_item_id=hit["knowledge_item_id"],
                    knowledge_version_id=hit["knowledge_version_id"],
                    rank=rank,
                    vector_score=hit.get("vector_score"),
                    keyword_score=hit.get("keyword_score"),
                    fused_score=hit.get("fused_score"),
                    citation_json=citation.model_dump(mode="json"),
                ),
            )
            out_hits.append(
                RetrievalHitOut(
                    rank=rank,
                    chunk_id=hit["chunk_id"],
                    content=hit["content"],
                    vector_score=hit.get("vector_score"),
                    keyword_score=hit.get("keyword_score"),
                    fused_score=hit.get("fused_score"),
                    citation=citation,
                ),
            )
        self.db.commit()

        try:
            from app.services.usage_service import UsageService

            UsageService(self.db).record(
                event_type="retrieval",
                user_id=user.id,
                project_id=body.project_id,
                provider=self.embedder.name,
                model=self.embedder.model,
                latency_ms=latency_ms,
                success=True,
                metadata={
                    "run_id": str(run.id),
                    "result_count": len(out_hits),
                    "insufficient_evidence": insufficient,
                },
                tenant_id=getattr(user, "active_tenant_id", None),
            )
        except Exception:
            pass

        return RetrievalSearchOut(
            run_id=run.id,
            query=query,
            insufficient_evidence=insufficient,
            embedding_provider=self.embedder.name,
            embedding_model=self.embedder.model,
            latency_ms=latency_ms,
            hits=out_hits,
        )

    def context(self, body: RetrievalSearchIn, user: User) -> RetrievalContextOut:
        result = self.search(body, user)
        blocks: list[str] = []
        for hit in result.hits:
            cite = hit.citation
            label = f"[{cite.title} · v{cite.version_label}"
            if cite.page_number is not None:
                label += f" · p{cite.page_number}"
            if cite.section_label:
                label += f" · {cite.section_label}"
            label += "]"
            blocks.append(f"{label}\n{hit.content}")
        assembled = "\n\n---\n\n".join(blocks)
        return RetrievalContextOut(
            run_id=result.run_id,
            query=result.query,
            insufficient_evidence=result.insufficient_evidence,
            review_required=result.insufficient_evidence,
            context_text=assembled,
            citations=[h.citation for h in result.hits],
            hits=result.hits,
            embedding_provider=result.embedding_provider,
            embedding_model=result.embedding_model,
            latency_ms=result.latency_ms,
            message=(
                "INSUFFICIENT EVIDENCE — REVIEW REQUIRED"
                if result.insufficient_evidence
                else None
            ),
        )

    def _eligible_filter_sql(
        self,
        body: RetrievalSearchIn,
        params: dict[str, Any],
        *,
        tenant_id: UUID | None = None,
    ) -> str:
        clauses = [
            "kv.status = ANY(:eligible_statuses)",
        ]
        params["eligible_statuses"] = list(RETRIEVAL_ELIGIBLE_STATUSES)
        if body.domain_code:
            clauses.append("ki.domain_code = :domain_code")
            params["domain_code"] = body.domain_code
        if body.knowledge_type:
            clauses.append("ki.knowledge_type = :knowledge_type")
            params["knowledge_type"] = body.knowledge_type
        if body.project_id:
            clauses.append("ki.project_id = :project_id")
            params["project_id"] = str(body.project_id)
        # Platform knowledge (NULL tenant) is shared; tenant-owned is isolated.
        if tenant_id is not None:
            clauses.append("(ki.tenant_id IS NULL OR ki.tenant_id = :tenant_id)")
            params["tenant_id"] = str(tenant_id)
        return " AND ".join(clauses)

    def _vector_search(
        self,
        query_vec: list[float],
        body: RetrievalSearchIn,
        *,
        limit: int,
        tenant_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "query_vec": str(query_vec)}
        where = self._eligible_filter_sql(body, params, tenant_id=tenant_id)
        sql = text(
            f"""
            SELECT
                kc.id AS chunk_id,
                kc.content,
                kc.page_number,
                kc.section_label,
                kc.chunk_index,
                kc.knowledge_item_id,
                kc.knowledge_version_id,
                ki.title,
                ki.domain_code,
                ki.knowledge_type,
                kv.version_label,
                kv.status,
                kv.source_document_name,
                1 - (kc.embedding <=> CAST(:query_vec AS vector)) AS vector_score
            FROM knowledge_chunks kc
            JOIN knowledge_versions kv ON kv.id = kc.knowledge_version_id
            JOIN knowledge_items ki ON ki.id = kc.knowledge_item_id
            WHERE kc.embedding IS NOT NULL
              AND {where}
            ORDER BY kc.embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
            """,
        )
        rows = self.db.execute(sql, params).mappings().all()
        return [dict(row) for row in rows]

    def _keyword_search(
        self,
        query: str,
        body: RetrievalSearchIn,
        *,
        limit: int,
        tenant_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "query": query}
        where = self._eligible_filter_sql(body, params, tenant_id=tenant_id)
        sql = text(
            f"""
            SELECT
                kc.id AS chunk_id,
                kc.content,
                kc.page_number,
                kc.section_label,
                kc.chunk_index,
                kc.knowledge_item_id,
                kc.knowledge_version_id,
                ki.title,
                ki.domain_code,
                ki.knowledge_type,
                kv.version_label,
                kv.status,
                kv.source_document_name,
                ts_rank_cd(kc.content_tsv, plainto_tsquery('english', :query)) AS keyword_score
            FROM knowledge_chunks kc
            JOIN knowledge_versions kv ON kv.id = kc.knowledge_version_id
            JOIN knowledge_items ki ON ki.id = kc.knowledge_item_id
            WHERE kc.content_tsv @@ plainto_tsquery('english', :query)
              AND {where}
            ORDER BY keyword_score DESC
            LIMIT :limit
            """,
        )
        rows = self.db.execute(sql, params).mappings().all()
        return [dict(row) for row in rows]

    @staticmethod
    def _rrf_fuse(
        vector_hits: list[dict[str, Any]],
        keyword_hits: list[dict[str, Any]],
        *,
        top_k: int,
        k: int = 60,
    ) -> list[dict[str, Any]]:
        scores: dict[Any, float] = {}
        merged: dict[Any, dict[str, Any]] = {}

        for rank, hit in enumerate(vector_hits, start=1):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            merged.setdefault(cid, dict(hit))
            merged[cid]["vector_score"] = float(hit.get("vector_score") or 0.0)

        for rank, hit in enumerate(keyword_hits, start=1):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            merged.setdefault(cid, dict(hit))
            merged[cid]["keyword_score"] = float(hit.get("keyword_score") or 0.0)

        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        out: list[dict[str, Any]] = []
        for cid, fused in ordered[:top_k]:
            row = merged[cid]
            row["fused_score"] = fused
            out.append(row)
        return out

    @staticmethod
    def _diversify(hits: list[dict[str, Any]], *, max_per_item: int) -> list[dict[str, Any]]:
        counts: dict[Any, int] = {}
        out: list[dict[str, Any]] = []
        for hit in hits:
            item_id = hit["knowledge_item_id"]
            if counts.get(item_id, 0) >= max_per_item:
                continue
            counts[item_id] = counts.get(item_id, 0) + 1
            out.append(hit)
        return out

    @staticmethod
    def _citation_from_hit(hit: dict[str, Any]) -> CitationOut:
        return CitationOut(
            knowledge_id=hit["knowledge_item_id"],
            knowledge_version_id=hit["knowledge_version_id"],
            chunk_id=hit["chunk_id"],
            title=hit.get("title") or "Untitled",
            version_label=str(hit.get("version_label") or ""),
            status=str(hit.get("status") or ""),
            domain_code=hit.get("domain_code"),
            knowledge_type=hit.get("knowledge_type"),
            page_number=hit.get("page_number"),
            section_label=hit.get("section_label"),
            source_document_name=hit.get("source_document_name"),
            excerpt=(hit.get("content") or "")[:400],
        )
