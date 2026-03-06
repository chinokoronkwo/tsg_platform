"use client";

import { useEffect, useState, useCallback } from "react";
import { DataTable, Column } from "@/components/data-tables/data-table";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004/api/v1";

interface AuditEntry {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string | null;
}

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const [actionFilter, setActionFilter] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set("skip", String(page * pageSize));
    params.set("limit", String(pageSize));
    if (actionFilter) params.set("action", actionFilter);
    if (resourceFilter) params.set("resource_type", resourceFilter);
    if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString());
    if (dateTo) params.set("date_to", new Date(dateTo).toISOString());

    try {
      const res = await fetch(`${API}/admin/audit-log?${params}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data.items ?? []);
        setTotal(data.total ?? 0);
      }
    } finally {
      setLoading(false);
    }
  }, [page, actionFilter, resourceFilter, dateFrom, dateTo]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const columns: Column<AuditEntry>[] = [
    {
      key: "created_at",
      header: "Date",
      sortable: true,
      render: (row) =>
        row.created_at
          ? new Date(row.created_at).toLocaleString()
          : "-",
    },
    { key: "user_id" as keyof AuditEntry, header: "User ID", sortable: true },
    { key: "action", header: "Action", sortable: true },
    { key: "resource_type", header: "Resource", sortable: true },
    { key: "resource_id" as keyof AuditEntry, header: "Resource ID" },
    {
      key: "details" as keyof AuditEntry,
      header: "Details",
      render: (row) =>
        row.details ? JSON.stringify(row.details).slice(0, 80) : "-",
    },
    { key: "ip_address" as keyof AuditEntry, header: "IP" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Audit Log</h1>
        <span className="text-cream/50 text-sm">{total} entries</span>
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-cream/60 mb-1">Action</label>
            <input
              type="text"
              placeholder="e.g. settings.change"
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Resource Type</label>
            <input
              type="text"
              placeholder="e.g. settings"
              value={resourceFilter}
              onChange={(e) => { setResourceFilter(e.target.value); setPage(0); }}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">From</label>
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(0); }}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">To</label>
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(0); }}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <p className="text-cream/50">Loading...</p>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={entries}
            keyExtractor={(r) => String(r.id)}
            pageSize={pageSize}
          />
          <div className="flex items-center gap-4 mt-4">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream disabled:opacity-30"
            >
              Previous
            </button>
            <span className="text-cream/60 text-sm">
              Page {page + 1} of {Math.ceil(total / pageSize) || 1}
            </span>
            <button
              disabled={(page + 1) * pageSize >= total}
              onClick={() => setPage((p) => p + 1)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream disabled:opacity-30"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
