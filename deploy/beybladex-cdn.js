const ORIGIN = "https://hkbeybladex.com";
const LONG_CACHE = "public, max-age=31536000, s-maxage=31536000, immutable";
const SHORT_CACHE = "public, max-age=60";
const ALLOWED_EXACT = new Set([
  "/logo.png",
  "/seo-image.png",
  "/og-card.jpg",
  "/alipayhk.jpg",
  "/favicon.ico",
]);

function allowedPath(path) {
  return (
    path.startsWith("/images/") ||
    path.startsWith("/parts-images/") ||
    ALLOWED_EXACT.has(path)
  );
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Max-Age": "86400",
  };
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }
    const url = new URL(request.url);
    if (!allowedPath(url.pathname)) {
      return new Response("Not found", { status: 404, headers: corsHeaders() });
    }
    const upstream = ORIGIN + url.pathname;
    const resp = await fetch(upstream, {
      method: request.method,
      cf: { cacheTtl: 31536000, cacheEverything: true },
    });
    const headers = new Headers(resp.headers);
    headers.set("Access-Control-Allow-Origin", "*");
    headers.set("X-Robots-Tag", "noindex, nofollow");
    headers.set("Cache-Control", resp.status === 200 ? LONG_CACHE : SHORT_CACHE);
    headers.delete("Set-Cookie");
    headers.delete("Expires");
    return new Response(request.method === "HEAD" ? null : resp.body, {
      status: resp.status,
      headers,
    });
  },
};
