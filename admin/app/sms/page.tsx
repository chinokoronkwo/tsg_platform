"use client";

type CampaignStatus = "Draft" | "Scheduled" | "Sent";

interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  sentCount: number;
  deliveryRate: number;
  createdAt: string;
}

const mockCampaigns: Campaign[] = [
  { id: "1", name: "Event Reminder - Wine Tasting", status: "Sent", sentCount: 120, deliveryRate: 98.5, createdAt: "2025-03-01" },
  { id: "2", name: "Weekly Newsletter", status: "Scheduled", sentCount: 0, deliveryRate: 0, createdAt: "2025-03-05" },
  { id: "3", name: "Membership Renewal", status: "Draft", sentCount: 0, deliveryRate: 0, createdAt: "2025-03-04" },
];

export default function SMSPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">SMS Campaign Manager</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          New Campaign
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Total Contacts</p>
          <p className="text-3xl font-bold text-white">2,450</p>
        </div>
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Active Campaigns</p>
          <p className="text-3xl font-bold text-white">1</p>
        </div>
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Messages Sent Today</p>
          <p className="text-3xl font-bold text-white">0</p>
        </div>
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Delivery Rate</p>
          <p className="text-3xl font-bold text-hunter">98.5%</p>
        </div>
      </div>

      <div className="bg-surface rounded-lg border border-cream/10 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-cream/10 bg-surface-2">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cream/60">Campaign</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cream/60">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cream/60">Sent</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cream/60">Delivery Rate</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-cream/60">Created</th>
            </tr>
          </thead>
          <tbody>
            {mockCampaigns.map((c) => (
              <tr key={c.id} className="border-b border-cream/5 hover:bg-cream/5">
                <td className="px-4 py-3 text-cream font-medium">{c.name}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      c.status === "Sent" ? "bg-hunter/30 text-hunter" : c.status === "Scheduled" ? "bg-secondary/20 text-secondary" : "bg-cream/20 text-cream/80"
                    }`}
                  >
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-cream/80">{c.sentCount}</td>
                <td className="px-4 py-3 text-cream/80">{c.deliveryRate ? `${c.deliveryRate}%` : "—"}</td>
                <td className="px-4 py-3 text-cream/60">{c.createdAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
