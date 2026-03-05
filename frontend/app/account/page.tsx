"use client";

import { useState } from "react";
import Link from "next/link";

const dashboardSections = [
  {
    title: "Orders",
    description: "View and track your orders",
    count: 0,
    href: "/account/orders",
  },
  {
    title: "Subscriptions",
    description: "Manage your subscriptions",
    count: 0,
    href: "/account/subscriptions",
  },
  {
    title: "Memberships",
    description: "Your membership details",
    count: 1,
    href: "/account/memberships",
  },
  {
    title: "Wallet",
    description: "Balance and transaction history",
    count: null,
    href: "/account/wallet",
  },
  {
    title: "Bookings",
    description: "Upcoming appointments",
    count: 2,
    href: "/account/bookings",
  },
  {
    title: "Courses",
    description: "Your learning progress",
    count: 3,
    href: "/account/courses",
  },
];

export default function AccountPage() {
  const [isAuthenticated] = useState(false);

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen pt-20 lg:pt-24 flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <h1 className="font-heading text-3xl lg:text-4xl text-white mb-4">
            My Account
          </h1>
          <p className="text-cream/80 mb-8">
            Please log in to access your account dashboard and manage your
            memberships, orders, and bookings.
          </p>
          <Link
            href="/login"
            className="inline-block bg-secondary text-white px-10 py-4 text-sm font-bold uppercase tracking-[0.2em] hover:bg-secondary/90 transition-colors"
          >
            Log In
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen pt-20 lg:pt-24">
      <section className="py-12 bg-primary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-heading text-4xl lg:text-5xl text-white mb-4">
            My Account
          </h1>
          <p className="text-cream/80 text-lg">
            Welcome back. Manage your memberships, orders, and more.
          </p>
        </div>
      </section>

      <section className="py-12 bg-surface">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dashboardSections.map((section) => (
              <Link
                key={section.title}
                href={section.href}
                className="block p-6 bg-primary border border-secondary/30 hover:border-secondary/60 transition-all duration-300 group"
              >
                <h2 className="font-heading text-xl text-white group-hover:text-secondary transition-colors mb-2">
                  {section.title}
                </h2>
                <p className="text-cream/80 text-sm mb-4">
                  {section.description}
                </p>
                <div className="flex items-center justify-between">
                  {section.count !== null && (
                    <span className="text-secondary text-sm font-medium">
                      {section.count} item{section.count !== 1 ? "s" : ""}
                    </span>
                  )}
                  <span className="text-cream/80 text-sm uppercase tracking-wider group-hover:text-secondary transition-colors">
                    View All →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
