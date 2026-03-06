import type { Metadata } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://thesnobgroup.com";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004/api/v1";

interface Props {
  params: Promise<{ slug: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const res = await fetch(`${API}/products/slug/${slug}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return {};
    const product = await res.json();
    return {
      title: product.seo_title || `${product.name} | Snob Group`,
      description:
        product.seo_description ||
        product.short_description ||
        product.description?.slice(0, 160),
      openGraph: {
        title: product.seo_title || product.name,
        description: product.seo_description || product.short_description || "",
        images: product.og_image_url ? [product.og_image_url] : [],
        url: `${BASE_URL}/shop/${slug}`,
      },
      twitter: { card: "summary_large_image" },
      alternates: { canonical: `${BASE_URL}/shop/${slug}` },
    };
  } catch {
    return {};
  }
}

export default function ProductLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
