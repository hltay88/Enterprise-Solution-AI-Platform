import { HomeAuthPanel } from "@/components/HomeAuthPanel";

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
          <HomeAuthPanel />
        </section>
      </main>
    </div>
  );
}
