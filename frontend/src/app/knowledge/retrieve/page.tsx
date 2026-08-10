"use client";

import { RetrievalExplorerView } from "@/components/RetrievalExplorerView";
import { RequireAuth } from "@/components/RequireAuth";

export default function RetrievalPage() {
  return (
    <RequireAuth>{(user) => <RetrievalExplorerView user={user} />}</RequireAuth>
  );
}
