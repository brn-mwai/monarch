/** @type {import('next').NextConfig} */

// BUILD_STATIC=1 emits a static export (`out/`) for Cloudflare Pages: no server,
// no edge runtime, no adapter. Unset builds the standalone Node bundle the
// Dockerfile uses. Security headers and image optimization need a server, so
// they only apply to the standalone build; on Cloudflare they are set via the
// dashboard / _headers instead.
const isStatic = process.env.BUILD_STATIC === "1";

const nextConfig = {
  productionBrowserSourceMaps: false,
  output: isStatic ? "export" : "standalone",
  images: { unoptimized: true },
  ...(isStatic
    ? { trailingSlash: true }
    : {
        async headers() {
          return [
            {
              source: "/(.*)",
              headers: [
                { key: "X-Frame-Options", value: "DENY" },
                { key: "X-Content-Type-Options", value: "nosniff" },
                { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
                { key: "X-XSS-Protection", value: "1; mode=block" },
                {
                  key: "Permissions-Policy",
                  value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
                },
              ],
            },
          ];
        },
      }),
};

export default nextConfig;
