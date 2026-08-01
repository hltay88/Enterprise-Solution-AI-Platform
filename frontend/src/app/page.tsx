import { HealthStatus } from "@/components/HealthStatus";

export default function HomePage() {
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          Project Atlas
          <span>Enterprise Solution AI Platform</span>
        </div>
      </header>
      <main className="main">
        <section className="hero">
          <h1>Requirement intelligence for enterprise solution teams</h1>
          <p>
            Sprint 1 frontend scaffold is ready. Login, dashboard, and project
            workflows arrive in Phase C.
          </p>
          <HealthStatus />
        </section>
      </main>
    </div>
  );
}
