import { AppHeader } from "@/components/AppHeader";
import { HomeAuthPanel } from "@/components/HomeAuthPanel";

export default function HomePage() {
  return (
    <div className="shell">
      <AppHeader showDashboardLink />
      <main className="main">
        <section className="hero">
          <h1>Requirement intelligence for enterprise solution teams</h1>
          <HomeAuthPanel />
        </section>
      </main>
    </div>
  );
}
