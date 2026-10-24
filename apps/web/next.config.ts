import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

// Netlify's OpenNext adapter handles the server output itself. Keep the
// standalone build for the optional self-hosted/Render path, but let Netlify
// use its native Next.js build output.
const isNetlifyBuild = process.env.NETLIFY === "true";

const nextConfig: NextConfig = {
  output: isNetlifyBuild ? undefined : "standalone",
  reactStrictMode: true,
  devIndicators: false,
  allowedDevOrigins: ["localhost", "127.0.0.1"],
};

export default withNextIntl(nextConfig);
