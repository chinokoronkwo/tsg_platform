import type { Metadata } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://thesnobgroup.com";

export const metadata: Metadata = {
  title: "Learn | Snob Group",
  description:
    "Explore courses and educational content on grooming, style, and the refined gentleman's lifestyle.",
  openGraph: {
    title: "Learn | Snob Group",
    description:
      "Explore courses and educational content on grooming, style, and the refined gentleman's lifestyle.",
    url: `${BASE_URL}/learn`,
  },
  alternates: { canonical: `${BASE_URL}/learn` },
};

export default function LearnLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
