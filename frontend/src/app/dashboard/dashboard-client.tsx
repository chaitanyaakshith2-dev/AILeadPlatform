"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

type Lead = {
  id: string;
  name: string;
  email: string | null;
  company: string | null;
  message: string;
  status: string;
  created_at: string;
  analysis: {
    lead_score: number;
    business_type: string;
    budget: string | null;
    timeline: string | null;
    requirements: string[];
    priority: "HIGH" | "MEDIUM" | "LOW";
    reasoning: string;
  } | null;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function DashboardClient({ email }: { email: string }) {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [leadEmail, setLeadEmail] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzingLeadId, setAnalyzingLeadId] = useState<string | null>(null);
  const [replyLeadId, setReplyLeadId] = useState<string | null>(null);
  const [suggestedReply, setSuggestedReply] = useState<string | null>(null);
  const [copiedReply, setCopiedReply] = useState(false);

  const apiRequest = useCallback(async (path: string, options?: RequestInit) => {
    const { data } = await createClient().auth.getSession();
    if (!data.session) {
      router.push("/login");
      throw new Error("Your session has expired");
    }

    return fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${data.session.access_token}`,
        ...options?.headers,
      },
    });
  }, [router]);

  useEffect(() => {
    async function loadLeads() {
      try {
        const response = await apiRequest("/leads");
        if (!response.ok) throw new Error("Could not load leads");
        setLeads(await response.json());
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Could not load leads");
      } finally {
        setLoading(false);
      }
    }

    void loadLeads();
  }, [apiRequest]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const response = await apiRequest("/leads", {
      method: "POST",
      body: JSON.stringify({ name, email: leadEmail || null, company: company || null, message }),
    });

    if (!response.ok) {
      setError("Could not create lead");
      return;
    }

    setLeads([await response.json(), ...leads]);
    setName("");
    setLeadEmail("");
    setCompany("");
    setMessage("");
    setShowForm(false);
  }

  async function handleLogout() {
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }

  async function handleAnalyze(leadId: string) {
    setAnalyzingLeadId(leadId);
    setError(null);
    try {
      const response = await apiRequest(`/leads/${leadId}/analyze`, { method: "POST" });
      if (!response.ok) throw new Error("Could not analyze lead");
      const analyzedLead = await response.json() as Lead;
      setLeads((currentLeads) => currentLeads.map((lead) => lead.id === leadId ? analyzedLead : lead));
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "Could not analyze lead");
    } finally {
      setAnalyzingLeadId(null);
    }
  }

  async function handleGenerateReply(leadId: string) {
    setReplyLeadId(leadId);
    setSuggestedReply(null);
    setCopiedReply(false);
    setError(null);
    try {
      const response = await apiRequest(`/leads/${leadId}/generate-reply`, { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(body?.detail ?? "Could not generate reply");
      }
      const body = await response.json() as { suggested_reply: string };
      setSuggestedReply(body.suggested_reply);
    } catch (replyError) {
      setError(replyError instanceof Error ? replyError.message : "Could not generate reply");
      setReplyLeadId(null);
    }
  }

  async function copyReply() {
    if (!suggestedReply) return;
    await navigator.clipboard.writeText(suggestedReply);
    setCopiedReply(true);
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">LeadFlow AI</p>
          <h1>Leads</h1>
          <p className="muted">{email}</p>
          <nav className="dashboard-nav"><span aria-current="page">Leads</span><Link href="/dashboard/settings">Settings</Link></nav>
        </div>
        <button type="button" className="secondary-button" onClick={handleLogout}>Log out</button>
      </header>

      <section className="dashboard-content">
        <div className="section-heading">
          <h2>Your leads</h2>
          <button type="button" onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add lead"}</button>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="lead-form">
            <label>Name<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
            <label>Email<input type="email" value={leadEmail} onChange={(event) => setLeadEmail(event.target.value)} /></label>
            <label>Company<input value={company} onChange={(event) => setCompany(event.target.value)} /></label>
            <label>Message<textarea value={message} onChange={(event) => setMessage(event.target.value)} required rows={4} /></label>
            <button type="submit">Save lead</button>
          </form>
        )}

        {error && <p className="error">{error}</p>}
        {suggestedReply && (
          <aside className="reply-panel" aria-live="polite">
            <div className="reply-panel-header">
              <div>
                <p className="eyebrow">AI follow-up</p>
                <h3>Suggested reply</h3>
              </div>
              <button type="button" className="secondary-button" onClick={() => { setSuggestedReply(null); setReplyLeadId(null); }}>Close</button>
            </div>
            <textarea className="reply-text" value={suggestedReply} readOnly rows={7} aria-label="Suggested follow-up reply" />
            <button type="button" onClick={() => void copyReply()}>{copiedReply ? "Copied" : "Copy reply"}</button>
          </aside>
        )}
        {loading ? <p className="muted">Loading leads...</p> : leads.length === 0 ? <p className="muted">No leads yet.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Company</th><th>Email</th><th>AI analysis</th><th>Message</th><th>Action</th></tr></thead>
              <tbody>{leads.map((lead) => <tr key={lead.id}>
                <td>{lead.name}</td>
                <td>{lead.company || "-"}</td>
                <td>{lead.email || "-"}</td>
                <td>
                  {lead.analysis ? <div className="analysis-summary">
                    <strong>{lead.analysis.lead_score}/100</strong>
                    <span className={`priority priority-${lead.analysis.priority.toLowerCase()}`}>{lead.analysis.priority}</span>
                    <span>{lead.analysis.business_type}</span>
                    <span>Budget: {lead.analysis.budget || "Unknown"}</span>
                    <span>Timeline: {lead.analysis.timeline || "Unknown"}</span>
                  </div> : <span className="muted">Not analyzed</span>}
                </td>
                <td>{lead.message}</td>
                <td>
                  {lead.analysis && <button type="button" onClick={() => void handleGenerateReply(lead.id)} disabled={replyLeadId === lead.id}>{replyLeadId === lead.id ? "Generating..." : "Generate AI Reply"}</button>}
                  {!lead.analysis && <button type="button" onClick={() => void handleAnalyze(lead.id)} disabled={analyzingLeadId === lead.id}>{analyzingLeadId === lead.id ? "Analyzing..." : "Analyze with AI"}</button>}
                </td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
