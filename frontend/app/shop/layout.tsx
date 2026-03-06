import type { Metadata } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://thesnobgroup.com";

export const metadata: Metadata = {
  title: "Shop | Snob Group",
  description:
    "Browse curated luxury grooming products, bespoke accessories, and exclusive merchandise from The Snob Group.",
  openGraph: {
    title: "Shop | Snob Group",
    description:
      "Browse curated luxury grooming products, bespoke accessories, and exclusive merchandise.",
    url: `${BASE_URL}/shop`,
  },
  alternates: { canonical: `${BASE_URL}/shop` },
};

export default function ShopLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
