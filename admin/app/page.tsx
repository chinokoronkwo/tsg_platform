export default function DashboardPage() {
  return (
    <div>
      <h1 className="font-heading text-4xl text-white mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard label="Total Revenue" value="$0" change="+0%" />
        <StatCard label="Active Members" value="0" change="+0%" />
        <StatCard label="Orders Today" value="0" change="+0%" />
        <StatCard label="LMS Enrollments" value="0" change="+0%" />
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

function StatCard({
  label,
  value,
  change,
}: {
  label: string;
  value: string;
  change: string;
}) {
  return (
    <div className="bg-surface rounded-lg p-6 border border-cream/10">
      <p className="text-cream/50 text-xs uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="text-hunter text-sm mt-1">{change}</p>
    </div>
  );
}
