# Phase 5 Architecture

Users → Web UI → API/Application → Atlas Orchestrator → Domain Services → Knowledge/Retrieval/Agent Services → Existing Requirement/Solution/Document Engines → Data/Object Storage.

Components: identity/tenant, knowledge, retrieval, agent orchestration, governance, collaboration, usage/observability.

Keep domain logic independent of LLM provider, vector database, cloud provider and UI framework.
