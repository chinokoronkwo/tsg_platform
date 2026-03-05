"use client";

import { useState } from "react";
import { DataTable, Column } from "@/components/data-tables/data-table";

type ProductType = "Physical" | "Digital" | "Subscription" | "Event";
type ProductStatus = "Draft" | "Active" | "Archived";

interface Product {
  id: string;
  image: string;
  name: string;
  type: ProductType;
  price: string;
  status: ProductStatus;
  stock: number;
}

const mockProducts: Product[] = [
  { id: "1", image: "", name: "Wine Tasting Experience", type: "Event", price: "$150", status: "Active", stock: 20 },
  { id: "2", image: "", name: "Premium Membership", type: "Subscription", price: "$49/mo", status: "Active", stock: -1 },
  { id: "3", image: "", name: "Sommelier Guide PDF", type: "Digital", price: "$29", status: "Active", stock: -1 },
  { id: "4", image: "", name: "Vintage Collection Box", type: "Physical", price: "$299", status: "Draft", stock: 50 },
];

export default function ProductsPage() {
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);

  const filtered = mockProducts.filter((p) => {
    if (typeFilter && p.type !== typeFilter) return false;
    if (statusFilter && p.status !== statusFilter) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const columns: Column<Product>[] = [
    {
      key: "image",
      header: "Image",
      width: "80px",
      render: (row) => (
        <div className="w-12 h-12 rounded bg-surface-2 border border-cream/10 flex items-center justify-center text-cream/40 text-xs">
          {row.image ? "img" : "—"}
        </div>
      ),
    },
    { key: "name", header: "Name", sortable: true },
    { key: "type", header: "Type", sortable: true },
    { key: "price", header: "Price", sortable: true },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            row.status === "Active"
              ? "bg-hunter/30 text-hunter"
              : row.status === "Draft"
              ? "bg-cream/20 text-cream/80"
              : "bg-cream/10 text-cream/50"
          }`}
        >
          {row.status}
        </span>
      ),
    },
    { key: "stock", header: "Stock", sortable: true, render: (row) => row.stock === -1 ? "∞" : row.stock },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <button className="text-secondary hover:text-secondary/80 text-sm">Edit</button>
          <button className="text-cream/60 hover:text-red-400 text-sm">Delete</button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Product Manager</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          Add Product
        </button>
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-cream/60 mb-1">Search</label>
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream placeholder-cream/40 focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="">All Types</option>
              <option value="Physical">Physical</option>
              <option value="Digital">Digital</option>
              <option value="Subscription">Subscription</option>
              <option value="Event">Event</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="">All Statuses</option>
              <option value="Draft">Draft</option>
              <option value="Active">Active</option>
              <option value="Archived">Archived</option>
            </select>
          </div>
        </div>
      </div>

      {selectedProducts.length > 0 && (
        <div className="flex items-center gap-4 mb-4 px-4 py-2 bg-surface-2 rounded-lg border border-cream/10">
          <span className="text-sm text-cream/80">{selectedProducts.length} selected</span>
          <button className="text-sm text-secondary hover:text-secondary/80">Bulk Edit</button>
          <button className="text-sm text-red-400 hover:text-red-300">Bulk Delete</button>
          <button onClick={() => setSelectedProducts([])} className="text-sm text-cream/60 hover:text-cream">Clear</button>
        </div>
      )}

      <DataTable
        columns={columns}
        data={filtered}
        keyExtractor={(r) => r.id}
        selectable
        onSelectionChange={setSelectedProducts}
      />
    </div>
  );
}
