"use client";

import dynamic from "next/dynamic";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, ArrowUpRight, Check, Copy, LogOut, Plus, Search, Settings2, Users, X, Zap } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import AiPulseButton from "@/components/ui/AiPulseButton";
import GlassCard from "@/components/ui/GlassCard";
import LeadTable3D, { type Lead } from "@/components/dashboard/LeadTable3D";

const HeroScene = dynamic(() => import("@/components/canvas/HeroScene"), { ssr: false });

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
      <header className="topbar"><Link className="brand" href="/dashboard"><span className="brand-mark"><Zap size={15} fill="currentColor" /></span>leadflow<span className="brand-ai">ai</span></Link><div className="topbar-actions"><span className="user-email">{email}</span><Link className="icon-button" href="/dashboard/settings" aria-label="Settings"><Settings2 size={17} /></Link><button type="button" className="icon-button" onClick={handleLogout} aria-label="Log out"><LogOut size={17} /></button></div></header>
      <section className="dashboard-hero"><div className="hero-copy"><p className="eyebrow"><span className="live-dot" /> AI-POWERED PIPELINE</p><h1>Turn interest into <em>momentum.</em></h1><p className="hero-description">Your intelligent command center for capturing, understanding, and converting every lead.</p><div className="hero-actions"><AiPulseButton onClick={() => setShowForm(true)}><Plus size={15} /> Add new lead</AiPulseButton><span className="shortcut"><span>⌘</span> K <span className="shortcut-label">Quick actions</span></span></div></div><div className="hero-visual"><HeroScene /><div className="hero-visual-label"><Activity size={14} /><span>Neural signal active</span><strong>98.4%</strong></div></div></section>

      <section className="dashboard-content">
        <div className="metrics-grid"><GlassCard className="metric-card" interactive={false}><span className="metric-icon cyan"><Users size={17} /></span><span className="metric-label">Total prospects</span><strong>{leads.length}</strong><small><span className="trend-up">+12.8%</span> this month</small></GlassCard><GlassCard className="metric-card" interactive={false}><span className="metric-icon violet"><Zap size={17} /></span><span className="metric-label">Avg. lead score</span><strong>{leads.length ? Math.round(leads.reduce((total, lead) => total + (lead.analysis?.lead_score ?? 0), 0) / leads.length) : 0}</strong><small><span className="trend-up">+8.2%</span> vs last month</small></GlassCard><GlassCard className="metric-card" interactive={false}><span className="metric-icon amber"><Activity size={17} /></span><span className="metric-label">Response rate</span><strong>84.6%</strong><small><span className="trend-up">+4.1%</span> this month</small></GlassCard><GlassCard className="metric-card signal-card" interactive={false}><div className="signal-wave"><span /><span /><span /><span /><span /></div><span className="metric-label">AI engine status</span><strong>Learning from your flow</strong><small><span className="live-dot" /> Processing signals in real time</small></GlassCard></div>
        <div className="section-heading"><div><p className="eyebrow">YOUR WORKSPACE</p><h2>Lead intelligence</h2></div><div className="section-tools"><div className="search-field"><Search size={15} /><input placeholder="Search leads..." aria-label="Search leads" /></div><button type="button" className="add-button" onClick={() => setShowForm(!showForm)}>{showForm ? <X size={16} /> : <Plus size={16} />}{showForm ? "Cancel" : "Add lead"}</button></div></div>

        {showForm && (
          <form onSubmit={handleSubmit} className="lead-form glass-card">
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
              <button type="button" className="icon-button" onClick={() => { setSuggestedReply(null); setReplyLeadId(null); }} aria-label="Close reply"><X size={16} /></button>
            </div>
            <textarea className="reply-text" value={suggestedReply} readOnly rows={7} aria-label="Suggested follow-up reply" />
            <button type="button" className="add-button" onClick={() => void copyReply()}>{copiedReply ? <Check size={15} /> : <Copy size={15} />}{copiedReply ? "Copied" : "Copy reply"}</button>
          </aside>
        )}
        {loading ? <p className="loading-state"><span className="loading-spinner" />Calibrating your pipeline...</p> : <LeadTable3D leads={leads} analyzingLeadId={analyzingLeadId} replyLeadId={replyLeadId} onAnalyze={(leadId) => void handleAnalyze(leadId)} onGenerateReply={(leadId) => void handleGenerateReply(leadId)} />}
      </section>
      <footer className="dashboard-footer"><span>Leadflow AI <span className="muted">/ Workspace</span></span><span>Built for focus <ArrowUpRight size={13} /></span></footer>
    </main>
  );
}
