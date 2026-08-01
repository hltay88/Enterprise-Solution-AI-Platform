import Link from "next/link";

import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <div className="shell">
      <header className="topbar">
        <Link href="/" className="brand brand-link">
          Project Atlas
          <span>Enterprise Solution AI Platform</span>
        </Link>
      </header>
      <main className="main">
        <section className="login-panel">
          <h1>Sign in</h1>
          <p>Access your enterprise solution workspace.</p>
          <LoginForm />
        </section>
      </main>
    </div>
  );
}
