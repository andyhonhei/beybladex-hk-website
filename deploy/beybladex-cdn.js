export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.hostname = "beybladex-watch.andyhhh.com";
    return fetch(new Request(url, request));
  },
};
