import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://thesnobgroup.com";
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: `${BASE_URL}/`, lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
    { url: `${BASE_URL}/shop`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE_URL}/memberships`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/learn`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.7 },
    { url: `${BASE_URL}/book`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
  ];

  let cmsPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API}/cms/pages?status=published&limit=100`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const data = await res.json();
      cmsPages = (data.items || []).map((p: { slug: string; updated_at: string }) => ({
        url: `${BASE_URL}/${p.slug}`,
        lastModified: new Date(p.updated_at),
        changeFrequency: "weekly" as const,
        priority: 0.6,
      }));
    }
  } catch {
    /* API unavailable — skip dynamic pages */
  }

  let productPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API}/products?limit=500`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const data = await res.json();
      productPages = (data.items || []).map((p: { slug: string; created_at: string }) => ({
        url: `${BASE_URL}/shop/${p.slug}`,
        lastModified: new Date(p.created_at),
        changeFrequency: "weekly" as const,
        priority: 0.7,
      }));
    }
  } catch {
    /* API unavailable — skip products */
  }

  return [...staticPages, ...cmsPages, ...productPages];
}
