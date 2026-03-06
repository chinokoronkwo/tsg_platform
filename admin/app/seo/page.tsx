"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface SEOData {
  id?: number;
  title: string;
  description: string;
  canonical_url: string;
  og_title: string;
  og_description: string;
  og_image: string;
  no_index: boolean;
  no_follow: boolean;
}

const emptySEO: SEOData = {
  title: "",
  description: "",
  canonical_url: "",
  og_title: "",
  og_description: "",
  og_image: "",
  no_index: false,
  no_follow: false,
};

export default function SEOPage() {
  const [mode, setMode] = useState<"page" | "entity">("page");
  const [pageId, setPageId] = useState("");
  const [entityType, setEntityType] = useState("product");
  const [entityId, setEntityId] = useState("");
  const [seo, setSeo] = useState<SEOData>({ ...emptySEO });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadSEO() {
    setLoading(true);
    setMessage("");
    const url =
      mode === "page"
        ? `${API}/cms/seo/page/${pageId}`
        : `${API}/cms/seo/entity/${entityType}/${entityId}`;
    try {
      const res = await fetch(url, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        if (data) {
          setSeo({
            id: data.id,
            title: data.title || "",
            description: data.description || "",
            canonical_url: data.canonical_url || "",
            og_title: data.og_title || "",
            og_description: data.og_description || "",
            og_image: data.og_image || "",
            no_index: data.no_index ?? false,
            no_follow: data.no_follow ?? false,
          });
        } else {
          setSeo({ ...emptySEO });
          setMessage("No SEO data found. Fill in the form to create.");
        }
      } else {
        setMessage("Failed to load SEO data.");
        setSeo({ ...emptySEO });
      }
    } catch {
      setMessage("Error loading SEO data.");
    } finally {
      setLoading(false);
    }
  }

  async function saveSEO() {
    setLoading(true);
    setMessage("");
    const url =
      mode === "page"
        ? `${API}/cms/seo/page/${pageId}`
        : `${API}/cms/seo/entity/${entityType}/${entityId}`;
    try {
      const res = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          title: seo.title || null,
          description: seo.description || null,
          canonical_url: seo.canonical_url || null,
          og_title: seo.og_title || null,
          og_description: seo.og_description || null,
          og_image: seo.og_image || null,
          no_index: seo.no_index,
          no_follow: seo.no_follow,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSeo({ ...seo, id: data.id });
        setMessage("SEO data saved successfully.");
      } else {
        setMessage("Failed to save SEO data.");
      }
    } catch {
      setMessage("Error saving SEO data.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="font-heading text-4xl text-white mb-8">SEO Management</h1>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex gap-4 items-end mb-4">
          <div>
            <label className="block text-xs text-cream/60 mb-1">Lookup Mode</label>
            <select
              value={mode}
              onChange={(e) => {
                setMode(e.target.value as "page" | "entity");
                setSeo({ ...emptySEO });
                setMessage("");
              }}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="page">CMS Page</option>
              <option value="entity">Entity (product, course, etc.)</option>
            </select>
          </div>

          {mode === "page" ? (
            <div>
              <label className="block text-xs text-cream/60 mb-1">Page ID</label>
              <input
                type="number"
                value={pageId}
                onChange={(e) => setPageId(e.target.value)}
                placeholder="e.g. 1"
                className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
              />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs text-cream/60 mb-1">Entity Type</label>
                <select
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value)}
                  className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
                >
                  <option value="product">Product</option>
                  <option value="course">Course</option>
                  <option value="membership">Membership</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-cream/60 mb-1">Entity ID</label>
                <input
                  type="number"
                  value={entityId}
                  onChange={(e) => setEntityId(e.target.value)}
                  placeholder="e.g. 1"
                  className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
                />
              </div>
            </>
          )}

          <button
            onClick={loadSEO}
            disabled={loading || (mode === "page" ? !pageId : !entityId)}
            className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors disabled:opacity-40"
          >
            Load
          </button>
        </div>

        {message && (
          <p className="text-sm text-cream/70 mb-4">{message}</p>
        )}
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs text-cream/60 mb-1">SEO Title</label>
            <input
              type="text"
              value={seo.title}
              onChange={(e) => setSeo({ ...seo, title: e.target.value })}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Canonical URL</label>
            <input
              type="text"
              value={seo.canonical_url}
              onChange={(e) => setSeo({ ...seo, canonical_url: e.target.value })}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-cream/60 mb-1">Meta Description</label>
            <textarea
              value={seo.description}
              onChange={(e) => setSeo({ ...seo, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">OG Title</label>
            <input
              type="text"
              value={seo.og_title}
              onChange={(e) => setSeo({ ...seo, og_title: e.target.value })}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">OG Image URL</label>
            <input
              type="text"
              value={seo.og_image}
              onChange={(e) => setSeo({ ...seo, og_image: e.target.value })}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-cream/60 mb-1">OG Description</label>
            <textarea
              value={seo.og_description}
              onChange={(e) => setSeo({ ...seo, og_description: e.target.value })}
              rows={2}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-cream text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={seo.no_index}
                onChange={(e) => setSeo({ ...seo, no_index: e.target.checked })}
                className="accent-secondary"
              />
              noindex
            </label>
            <label className="flex items-center gap-2 text-cream text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={seo.no_follow}
                onChange={(e) => setSeo({ ...seo, no_follow: e.target.checked })}
                className="accent-secondary"
              />
              nofollow
            </label>
          </div>
        </div>

        <button
          onClick={saveSEO}
          disabled={loading}
          className="px-6 py-2 bg-hunter text-white font-semibold rounded-lg hover:bg-hunter/90 transition-colors disabled:opacity-40"
        >
          {loading ? "Saving..." : "Save SEO Data"}
        </button>
      </div>
    </div>
  );
}
