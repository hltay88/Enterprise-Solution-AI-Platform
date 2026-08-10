"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { clearAccessToken } from "@/lib/auth";

type AppHeaderProps = {
  userName?: string;
  showDashboardLink?: boolean;
  showKnowledgeLink?: boolean;
};

export function AppHeader({
  userName,
  showDashboardLink = false,
  showKnowledgeLink = false,
}: AppHeaderProps) {
  const router = useRouter();

  function signOut() {
    clearAccessToken();
    router.replace("/login");
  }

  return (
    <header className="topbar">
      <Link href={userName ? "/dashboard" : "/"} className="brand brand-link">
        Project Atlas
        <span>Enterprise Solution AI Platform</span>
      </Link>
      <nav className="topnav">
        {showDashboardLink ? (
          <Link className="nav-link" href="/dashboard">
            Dashboard
          </Link>
        ) : null}
        {showKnowledgeLink || userName ? (
          <Link className="nav-link" href="/knowledge">
            Knowledge
          </Link>
        ) : null}
        {userName ? (
          <Link className="nav-link" href="/solutions">
            Solutions
          </Link>
        ) : null}
        {userName ? (
          <Link className="nav-link" href="/approvals">
            Approvals
          </Link>
        ) : null}
        {userName ? (
          <Link className="nav-link" href="/usage">
            Usage
          </Link>
        ) : null}
        {userName ? (
          <Link className="nav-link" href="/governance">
            Audit
          </Link>
        ) : null}
        {userName ? (
          <Link className="nav-link" href="/tenants">
            Tenant
          </Link>
        ) : null}
        {userName ? (
          <>
            <span className="nav-user">{userName}</span>
            <button className="btn-secondary btn-compact" type="button" onClick={signOut}>
              Sign out
            </button>
          </>
        ) : (
          <Link className="btn-primary btn-compact" href="/login">
            Sign in
          </Link>
        )}
      </nav>
    </header>
  );
}
