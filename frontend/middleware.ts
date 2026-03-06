import { NextRequest, NextResponse } from "next/server";

const API = process.env.NEXT_PUBLIC_API_URL || "http://backend:8000/api/v1";

let redirectCache: Map<string, { target: string; status: number }> | null = null;
let cacheTime = 0;
const CACHE_TTL = 60_000;

async function loadRedirects() {
  const now = Date.now();
  if (redirectCache && now - cacheTime < CACHE_TTL) return redirectCache;
  try {
    const res = await fetch(`${API}/cms/redirects?limit=200`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      const data = await res.json();
      const map = new Map<string, { target: string; status: number }>();
      for (const r of data.items || []) {
        map.set(r.source_path, {
          target: r.target_path,
          status: r.status_code,
        });
      }
      redirectCache = map;
      cacheTime = now;
      return map;
    }
  } catch {
    /* API unavailable */
  }
  return redirectCache ?? new Map();
}

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const redirects = await loadRedirects();
  const match = redirects.get(path);
  if (match) {
    const url = match.target.startsWith("http")
      ? match.target
      : new URL(match.target, request.url).toString();
    return NextResponse.redirect(url, { status: match.status });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|api|static|favicon.ico|.*\\..*).*)"],
};
