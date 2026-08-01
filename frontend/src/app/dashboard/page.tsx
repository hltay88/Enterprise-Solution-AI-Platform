import { DashboardView } from "@/components/DashboardView";
import { RequireAuth } from "@/components/RequireAuth";

export default function DashboardPage() {
  return <RequireAuth>{(user) => <DashboardView user={user} />}</RequireAuth>;
}
