"use client";

type CampaignStatus = "Draft" | "Scheduled" | "Sent";

interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  sentCount: number;
  openRate: number;
  clickRate: number;
  createdAt: string;
}

const mockCampaigns: Campaign[] = [
  { id: "1", name: "March Newsletter", status: "Sent", sentCount: 1250, openRate: 42, clickRate: 8.5, createdAt: "2025-03-01" },
  { id: "2", name: "Event Invitation", status: "Scheduled", sentCount: 0, openRate: 0, clickRate: 0, createdAt: "2025-03-05" },
  { id: "3", name: "Welcome Series", status: "Draft", sentCount: 0, openRate: 0, clickRate: 0, createdAt: "2025-03-04" },
];

export default function EmailPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-heading text-4xl text-white">Email Campaign Manager</h1>
        <button className="px-4 py-2 bg-secondary text-primary font-semibold rounded-lg hover:bg-secondary/90 transition-colors">
          New Campaign
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Subscribers</p>
          <p className="text-3xl font-bold text-white">3,240</p>
        </div>
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Active Campaigns</p>
          <p className="text-3xl font-bold text-white">1</p>
        </div>
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">Avg. Open Rate</p>
          <p className="text-3xl font-bold text-hunter">38%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <h2 className="font-heading text-lg text-white mb-4">Campaigns</h2>
          <div className="space-y-3">
            {mockCampaigns.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between p-4 rounded-lg bg-surface-2 border border-cream/10"
              >
                <div>
                  <p className="font-medium text-cream">{c.name}</p>
                  <p className="text-sm text-cream/50">
                    {c.sentCount > 0 ? `${c.sentCount} sent · ${c.openRate}% open · ${c.clickRate}% click` : "Not sent"}
                  </p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    c.status === "Sent" ? "bg-hunter/30 text-hunter" : c.status === "Scheduled" ? "bg-secondary/20 text-secondary" : "bg-cream/20 text-cream/80"
                  }`}
                >
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-cream/10 p-6">
          <h2 className="font-heading text-lg text-white mb-4">Templates</h2>
          <div className="space-y-3">
            <div className="p-4 rounded-lg bg-surface-2 border border-cream/10 flex items-center justify-between">
              <p className="text-cream">Newsletter Template</p>
              <button className="text-sm text-secondary hover:text-secondary/80">Edit</button>
            </div>
            <div className="p-4 rounded-lg bg-surface-2 border border-cream/10 flex items-center justify-between">
              <p className="text-cream">Event Invitation</p>
              <button className="text-sm text-secondary hover:text-secondary/80">Edit</button>
            </div>
            <button className="w-full py-2 border border-dashed border-cream/20 rounded-lg text-cream/50 hover:text-cream hover:border-cream/40 text-sm">
              + Add Template
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
