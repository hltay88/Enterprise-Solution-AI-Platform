"use client";

import { KnowledgeLibraryView } from "@/components/KnowledgeLibraryView";
import { RequireAuth } from "@/components/RequireAuth";

export default function KnowledgePage() {
  return (
    <RequireAuth>{(user) => <KnowledgeLibraryView user={user} />}</RequireAuth>
  );
}
