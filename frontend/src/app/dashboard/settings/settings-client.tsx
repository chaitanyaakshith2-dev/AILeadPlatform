"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

type Settings = {
  business_name: string;
  services_offered: string;
  reply_signature: string;
  webhook_url: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function SettingsClient() {
  const router = useRouter();
  const [settings, setSettings] = useState<Settings>({ business_name: "", services_offered: "", reply_signature: "", webhook_url: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiRequest = useCallback(async (options?: RequestInit) => {
    const { data } = await createClient().auth.getSession();
    if (!data.session) {
      router.push("/login");
      throw new Error("Your session has expired");
    }
    return fetch(`${apiBaseUrl}/settings`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${data.session.access_token}`,
        ...options?.headers,
      },
    });
  }, [router]);

  useEffect(() => {
    async function loadSettings() {
      try {
        const response = await apiRequest();
        if (!response.ok) throw new Error("Could not load settings");
        setSettings(await response.json());
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Could not load settings");
      } finally {
        setLoading(false);
      }
    }
    void loadSettings();
  }, [apiRequest]);

  async function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await apiRequest({
        method: "PUT",
        body: JSON.stringify({
          business_name: settings.business_name,
          services_offered: settings.services_offered,
          reply_signature: settings.reply_signature,
        }),
      });
      if (!response.ok) throw new Error("Could not save settings");
      setSettings(await response.json());
      setMessage("Settings saved.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save settings");
    } finally {
      setSaving(false);
    }
  }

  async function copyWebhookUrl() {
    await navigator.clipboard.writeText(settings.webhook_url);
    setCopied(true);
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">LeadFlow AI</p>
          <h1>Settings</h1>
          <nav className="dashboard-nav"><Link href="/dashboard">Leads</Link><span aria-current="page">Settings</span></nav>
        </div>
      </header>
      <section className="dashboard-content settings-content">
        <h2>Business profile</h2>
        <p className="muted">This context helps AI draft replies in your voice.</p>
        {loading ? <p className="muted">Loading settings...</p> : <form onSubmit={saveSettings} className="lead-form">
          <label>Business name<input value={settings.business_name} onChange={(event) => setSettings({ ...settings, business_name: event.target.value })} /></label>
          <label>Services offered<textarea value={settings.services_offered} onChange={(event) => setSettings({ ...settings, services_offered: event.target.value })} rows={4} placeholder="Web design, branding, consulting..." /></label>
          <label>Reply signature<textarea value={settings.reply_signature} onChange={(event) => setSettings({ ...settings, reply_signature: event.target.value })} rows={3} placeholder="Best, Alex from Example Co" /></label>
          {error && <p className="error">{error}</p>}
          {message && <p className="success">{message}</p>}
          <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save settings"}</button>
        </form>}
        {!loading && <div className="webhook-panel">
          <h2>Public lead capture</h2>
          <p className="muted">Send POST requests with name, email, company, and message to this URL.</p>
          <div className="webhook-row"><input value={settings.webhook_url} readOnly aria-label="Public lead capture webhook URL" /><button type="button" onClick={() => void copyWebhookUrl()}>{copied ? "Copied" : "Copy URL"}</button></div>
        </div>}
      </section>
    </main>
  );
}
