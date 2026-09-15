"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const { error: signInError } = await createClient().auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      setError(signInError.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <p className="eyebrow">LeadFlow AI</p>
        <h1>Log in</h1>
        <p className="muted">Access your leads workspace.</p>
        <form onSubmit={handleSubmit} className="stack-form">
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={6} />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>{loading ? "Logging in..." : "Log in"}</button>
        </form>
        <p className="muted">New here? <Link href="/signup">Create an account</Link></p>
      </section>
    </main>
  );
}
