import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "thesnobgroup.com" },
    ],
  },
};

export default nextConfig;
