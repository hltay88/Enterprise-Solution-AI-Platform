"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { ProjectForm } from "@/components/ProjectForm";
import { RequireAuth } from "@/components/RequireAuth";
import { apiPost, ApiClientError } from "@/lib/api";
import type { ProjectInput, ProjectSummary } from "@/lib/types";

function NewProjectContent({ userName }: { userName: string }) {
  const router = useRouter();

  async function handleCreate(values: ProjectInput) {
    try {
      const project = await apiPost<ProjectSummary>("/api/projects", values, true);
      router.replace(`/projects/${project.id}`);
    } catch (error) {
      throw new Error(
        error instanceof ApiClientError ? error.message : "Unable to create project",
      );
    }
  }

  return (
    <div className="shell">
      <AppHeader userName={userName} />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/dashboard">← Back to dashboard</Link>
          </p>
          <h1>New project</h1>
          <p>Create a project to capture customer requirements and analysis.</p>
        </section>
        <section className="form-panel">
          <ProjectForm submitLabel="Create project" onSubmit={handleCreate} />
        </section>
      </main>
    </div>
  );
}

export default function NewProjectPage() {
  return (
    <RequireAuth>
      {(user) => <NewProjectContent userName={user.name} />}
    </RequireAuth>
  );
}
