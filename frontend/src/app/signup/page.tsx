"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    const { data, error: signUpError } = await createClient().auth.signUp({ email, password });
    if (signUpError) {
      setError(signUpError.message);
      setLoading(false);
      return;
    }

    if (data.session) {
      router.push("/dashboard");
      router.refresh();
      return;
    }

    setMessage("Check your email to confirm your account, then log in.");
    setLoading(false);
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <p className="eyebrow">LeadFlow AI</p>
        <h1>Create account</h1>
        <p className="muted">Start managing your business leads.</p>
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
          {message && <p className="success">{message}</p>}
          <button type="submit" disabled={loading}>{loading ? "Creating..." : "Create account"}</button>
        </form>
        <p className="muted">Already have an account? <Link href="/login">Log in</Link></p>
      </section>
    </main>
  );
}
