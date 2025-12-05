import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Base path for GitHub Pages (adjust if using custom domain)
  // basePath: '/rastraverba',
  trailingSlash: true,
};

export default nextConfig;
