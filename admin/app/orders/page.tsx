"use client";

import { useState } from "react";
import { DataTable, Column } from "@/components/data-tables/data-table";

type OrderStatus = "Pending" | "Paid" | "Shipped" | "Delivered" | "Cancelled";

interface Order {
  id: string;
  orderNumber: string;
  customer: string;
  date: string;
  status: OrderStatus;
  total: string;
}

const mockOrders: Order[] = [
  { id: "1", orderNumber: "SG-1001", customer: "Jane Smith", date: "2025-03-04", status: "Paid", total: "$299" },
  { id: "2", orderNumber: "SG-1002", customer: "John Doe", date: "2025-03-03", status: "Shipped", total: "$150" },
  { id: "3", orderNumber: "SG-1003", customer: "Alice Brown", date: "2025-03-02", status: "Pending", total: "$49" },
  { id: "4", orderNumber: "SG-1004", customer: "Bob Wilson", date: "2025-03-01", status: "Delivered", total: "$89" },
];

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const filtered = mockOrders.filter((o) => {
    if (statusFilter && o.status !== statusFilter) return false;
    if (dateFrom && o.date < dateFrom) return false;
    if (dateTo && o.date > dateTo) return false;
    return true;
  });

  const columns: Column<Order>[] = [
    { key: "orderNumber", header: "Order #", sortable: true },
    { key: "customer", header: "Customer", sortable: true },
    { key: "date", header: "Date", sortable: true },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            row.status === "Paid" || row.status === "Shipped" || row.status === "Delivered"
              ? "bg-hunter/30 text-hunter"
              : row.status === "Pending"
              ? "bg-secondary/20 text-secondary"
              : "bg-cream/10 text-cream/50"
          }`}
        >
          {row.status}
        </span>
      ),
    },
    { key: "total", header: "Total", sortable: true },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <button
          onClick={() => setSelectedOrder(row)}
          className="text-secondary hover:text-secondary/80 text-sm"
        >
          View
        </button>
      ),
    },
  ];

  return (
    <div>
      <h1 className="font-heading text-4xl text-white mb-8">Order Manager</h1>

      <div className="bg-surface rounded-lg border border-cream/10 p-6 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-cream/60 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            >
              <option value="">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Paid">Paid</option>
              <option value="Shipped">Shipped</option>
              <option value="Delivered">Delivered</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/60 mb-1">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-4 py-2 bg-surface-2 border border-cream/10 rounded-lg text-cream focus:outline-none focus:ring-2 focus:ring-secondary/50"
            />
          </div>
        </div>
      </div>

      <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />

      {selectedOrder && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedOrder(null)}
        >
          <div
            className="bg-surface rounded-lg border border-cream/10 p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-heading text-xl text-white mb-4">Order {selectedOrder.orderNumber}</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-cream/60">Customer</dt>
                <dd className="text-cream">{selectedOrder.customer}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-cream/60">Date</dt>
                <dd className="text-cream">{selectedOrder.date}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-cream/60">Status</dt>
                <dd className="text-cream">{selectedOrder.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-cream/60">Total</dt>
                <dd className="text-secondary font-semibold">{selectedOrder.total}</dd>
              </div>
            </dl>
            <div className="mt-6 flex gap-2">
              <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90">
                Update Status
              </button>
              <button
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 bg-surface-2 border border-cream/10 text-cream rounded-lg hover:bg-cream/5"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
