"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navSections = [
  {
    label: "Overview",
    items: [{ href: "/", label: "Dashboard", icon: "◉" }],
  },
  {
    label: "Content",
    items: [
      { href: "/pages", label: "Pages", icon: "📄" },
      { href: "/media", label: "Media Library", icon: "🖼" },
      { href: "/menus", label: "Menus", icon: "☰" },
      { href: "/seo", label: "SEO", icon: "🔍" },
    ],
  },
  {
    label: "Commerce",
    items: [
      { href: "/products", label: "Products", icon: "🏷" },
      { href: "/events", label: "Events", icon: "📅" },
      { href: "/orders", label: "Orders", icon: "📦" },
      { href: "/subscriptions", label: "Subscriptions", icon: "🔁" },
      { href: "/memberships", label: "Memberships", icon: "💎" },
      { href: "/wallet", label: "Wallet", icon: "💰" },
    ],
  },
  {
    label: "Learning",
    items: [
      { href: "/courses", label: "Courses", icon: "🎓" },
      { href: "/cohorts", label: "Cohorts", icon: "👥" },
      { href: "/students", label: "Students", icon: "📊" },
    ],
  },
  {
    label: "Communications",
    items: [
      { href: "/email", label: "Email Campaigns", icon: "✉" },
      { href: "/sms", label: "SMS Campaigns", icon: "💬" },
    ],
  },
  {
    label: "People",
    items: [
      { href: "/users", label: "Users", icon: "👤" },
      { href: "/roles", label: "Roles & Permissions", icon: "🔐" },
      { href: "/bookings", label: "Bookings", icon: "📋" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/audit-log", label: "Audit Log", icon: "📜" },
      { href: "/backups", label: "Backups", icon: "💾" },
      { href: "/settings", label: "Settings", icon: "⚙" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 w-64 h-screen bg-surface overflow-y-auto border-r border-cream/10">
      <div className="p-6 border-b border-cream/10">
        <Link href="/" className="block">
          <h1 className="font-heading text-2xl text-white tracking-wide">
            Snob Group
          </h1>
          <p className="text-xs text-secondary uppercase tracking-[0.2em] mt-1">
            Admin Portal
          </p>
        </Link>
      </div>

      <nav className="py-4">
        {navSections.map((section) => (
          <div key={section.label} className="mb-2">
            <h3 className="px-6 py-2 text-[10px] font-bold uppercase tracking-[0.15em] text-cream/40">
              {section.label}
            </h3>
            {section.items.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-6 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-hunter/20 text-secondary border-r-2 border-secondary"
                      : "text-cream/70 hover:bg-cream/5 hover:text-cream"
                  }`}
                >
                  <span className="text-base">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
}
