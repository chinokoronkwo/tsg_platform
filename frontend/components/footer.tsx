"use client";

import Link from "next/link";
import { useState } from "react";

const quickLinks = [
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/terms", label: "Terms" },
];

const socialLinks = [
  { href: "#", label: "Instagram" },
  { href: "#", label: "LinkedIn" },
  { href: "#", label: "Twitter" },
];

export function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubscribed(true);
      setEmail("");
    }
  };

  return (
    <footer className="bg-primary border-t border-secondary/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          {/* Company info */}
          <div className="lg:col-span-1">
            <Link
              href="/"
              className="font-heading text-2xl text-secondary tracking-[0.2em]"
            >
              SNOB GROUP
            </Link>
            <p className="mt-4 text-cream/80 text-sm leading-relaxed">
              The exclusive boutique grooming club. A personalized luxury
              experience focusing on the sartorial, tonsorial and cordwainer needs
              of our clients.
            </p>
          </div>

          {/* Quick links */}
          <div>
            <h3 className="font-heading text-lg text-secondary uppercase tracking-wider mb-4">
              Quick Links
            </h3>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-cream/80 text-sm hover:text-secondary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Social links */}
          <div>
            <h3 className="font-heading text-lg text-secondary uppercase tracking-wider mb-4">
              Connect
            </h3>
            <div className="flex gap-4">
              {socialLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-cream/80 hover:text-secondary transition-colors text-sm font-medium uppercase tracking-wider"
                  aria-label={link.label}
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          {/* Newsletter */}
          <div>
            <h3 className="font-heading text-lg text-secondary uppercase tracking-wider mb-4">
              Newsletter
            </h3>
            {subscribed ? (
              <p className="text-cream/80 text-sm">
                Thank you for subscribing to our newsletter.
              </p>
            ) : (
              <form onSubmit={handleNewsletterSubmit} className="space-y-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full px-4 py-2 bg-surface border border-secondary/30 text-cream placeholder-cream/50 focus:outline-none focus:border-secondary transition-colors"
                  required
                />
                <button
                  type="submit"
                  className="w-full py-2 bg-secondary text-white text-sm font-medium uppercase tracking-wider hover:bg-secondary/90 transition-colors"
                >
                  Subscribe
                </button>
              </form>
            )}
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-secondary/20">
          <p className="text-cream/60 text-sm text-center">
            © {new Date().getFullYear()} Snob Group. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
