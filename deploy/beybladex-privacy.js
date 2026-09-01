const PRIVACY_PATHS = new Set(["/privacy", "/terms"]);

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (!PRIVACY_PATHS.has(url.pathname)) {
      return new Response("Not found", { status: 404 });
    }
    url.hostname = "beybladex-watch.andyhhh.com";
    return fetch(new Request(url, request));
  },
};
