"use client";

import { useState } from "react";
import { DataTable, Column } from "@/components/data-tables/data-table";

interface AuditEntry {
  id: string;
  date: string;
  user: string;
  action: string;
  resource: string;
  details: string;
}

const mockLogs: AuditEntry[] = [
  { id: "1", date: "2025-03-04 14:32", user: "Jane Smith", action: "Updated", resource: "Product", details: "Wine Tasting Experience - price changed" },
  { id: "2", date: "2025-03-04 11:15", user: "Alice Brown", action: "Created", resource: "Event", details: "Sommelier Workshop" },
  { id: "3", date: "2025-03-03 16:45", user: "Jane Smith", action: "Deleted", resource: "Media", details: "old-banner.jpg" },
  { id: "4", date: "2025-03-03 09:20", user: "John Doe", action: "Login", resource: "Auth", details: "Successful login" },
];

export default function AuditLogPage() {
  const [userFilter, setUserFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const filtered = mockLogs.filter((l) => {
    if (userFilter && !l.user.toLowerCase().includes(userFilter.toLowerCase())) return false;
    if (actionFilter && l.action !== actionFilter) return false;
    if (dateFrom && l.date < dateFrom) return false;
    if (dateTo && l.date > dateTo) return false;
    return true;
  });

  const columns: Column<AuditEntry>[] = [
    { key: "date", header: "Date", sortable: true },
    { key: "user", header: "User", sortable: true },
    { key: "action", header: "Action", sortable: true },
    { key: "resource", header: "Resource", sortable: true },
    { key: "details", header: "Details" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Audit Log</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Export
        </button>
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-cream/60 mb-1">User</label>
            <input
              type="text"
              placeholder="Filter by user..."
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Action Type</label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="">All Actions</option>
              <option value="Created">Created</option>
              <option value="Updated">Updated</option>
              <option value="Deleted">Deleted</option>
              <option value="Login">Login</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">From</label>
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">To</label>
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
        </div>
      </div>

      <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} pageSize={20} />
    </div>
  );
}
