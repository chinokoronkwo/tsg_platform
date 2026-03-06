"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004/api/v1";

interface DashboardStats {
  total_users: number;
  active_memberships: number;
  total_orders: number;
  total_revenue: number;
  total_enrollments: number;
  active_courses: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    fetch(`${API}/admin/dashboard`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setStats(data);
      });
  }, []);

  if (!stats) {
    return (
      <div>
        <h1 className="font-heading text-4xl text-white mb-8">Dashboard</h1>
        <p className="text-cream/50">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-heading text-4xl text-white mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          label="Total Users"
          value={String(stats.total_users)}
        />
        <StatCard
          label="Active Memberships"
          value={String(stats.active_memberships)}
        />
        <StatCard
          label="Total Orders"
          value={String(stats.total_orders)}
        />
        <StatCard
          label="Total Revenue"
          value={`$${stats.total_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
        />
        <StatCard
          label="LMS Enrollments"
          value={String(stats.total_enrollments)}
        />
        <StatCard
          label="Active Courses"
          value={String(stats.active_courses)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface rounded-lg p-6 border border-cream/10">
          <h2 className="text-lg font-bold text-white mb-4">Recent Orders</h2>
          <p className="text-cream/50 text-sm">No orders yet.</p>
        </div>
        <div className="bg-surface rounded-lg p-6 border border-cream/10">
          <h2 className="text-lg font-bold text-white mb-4">Recent Activity</h2>
          <p className="text-cream/50 text-sm">No activity yet.</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface rounded-lg p-6 border border-cream/10">
      <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
