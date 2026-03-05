"use client";

import { useState } from "react";
import { DataTable, Column } from "@/components/data-tables/data-table";

type UserRole = "Admin" | "Editor" | "Member" | "Guest";

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: UserRole;
  membership: string;
  lastLogin: string;
}

const mockUsers: User[] = [
  { id: "1", name: "Jane Smith", email: "jane@example.com", avatar: "", role: "Admin", membership: "Premium", lastLogin: "2025-03-04 14:30" },
  { id: "2", name: "John Doe", email: "john@example.com", avatar: "", role: "Member", membership: "Basic", lastLogin: "2025-03-03 09:15" },
  { id: "3", name: "Alice Brown", email: "alice@example.com", avatar: "", role: "Editor", membership: "Premium", lastLogin: "2025-03-04 11:00" },
];

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");

  const filtered = mockUsers.filter((u) => {
    if (search && !u.name.toLowerCase().includes(search.toLowerCase()) && !u.email.toLowerCase().includes(search.toLowerCase())) return false;
    if (roleFilter && u.role !== roleFilter) return false;
    return true;
  });

  const columns: Column<User>[] = [
    {
      key: "avatar",
      header: "",
      width: "48px",
      render: (row) => (
        <div className="w-10 h-10 rounded-full bg-surface-2 border border-cream/10 flex items-center justify-center text-cream/60 text-sm font-semibold">
          {row.name.charAt(0)}
        </div>
      ),
    },
    { key: "name", header: "Name", sortable: true },
    { key: "email", header: "Email", sortable: true },
    {
      key: "role",
      header: "Role",
      render: (row) => (
        <span className="px-2 py-0.5 rounded text-xs bg-secondary/20 text-secondary">
          {row.role}
        </span>
      ),
    },
    { key: "membership", header: "Membership", sortable: true },
    { key: "lastLogin", header: "Last Login", sortable: true },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <button className="text-secondary hover:text-secondary/80 text-sm">Impersonate</button>
          <button className="text-cream/60 hover:text-cream text-sm">Edit</button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">User Management</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Add User
        </button>
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-cream/60 mb-1">Search</label>
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Role</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="">All Roles</option>
              <option value="Admin">Admin</option>
              <option value="Editor">Editor</option>
              <option value="Member">Member</option>
              <option value="Guest">Guest</option>
            </select>
          </div>
        </div>
      </div>

      <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />
    </div>
  );
}
