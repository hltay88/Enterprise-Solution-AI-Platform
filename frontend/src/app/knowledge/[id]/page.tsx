"use client";

import { use } from "react";

import { KnowledgeDetailView } from "@/components/KnowledgeDetailView";
import { RequireAuth } from "@/components/RequireAuth";

export default function KnowledgeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <RequireAuth>
      {(user) => <KnowledgeDetailView user={user} knowledgeId={id} />}
    </RequireAuth>
  );
}
