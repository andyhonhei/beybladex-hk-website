const HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Policy · HK BeybladeX Watch</title>
<meta name="description" content="Privacy policy for HK BeybladeX Watch stock alerts and website analytics.">
<link rel="canonical" href="https://hkbeybladex.com/privacy">
</head>
<body>
<h1>Privacy Policy</h1>
<p>Last updated: 1 September 2026</p>
<p>This policy applies to <a href="https://hkbeybladex.com">https://hkbeybladex.com</a> and the related Threads, Telegram, and Discord stock-alert channels operated as HK BeybladeX Watch. The project is unofficial and not affiliated with Takara Tomy.</p>
<h2>What this service is</h2>
<p>We watch public Hong Kong hobby-shop websites for Beyblade X stock changes and show that information on this site. Optional alerts go to Discord, Telegram, and Threads.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Website analytics.</strong> Pages load Google Analytics (gtag). Google may receive your IP address, browser type, pages viewed, and similar usage data under Google’s own policy.</li>
<li><strong>Admin login.</strong> The separate admin host uses an HttpOnly session cookie so the operator can send a test notification. Visitors of the public site do not get this cookie.</li>
<li><strong>Shop data.</strong> Product names, prices, stock status, and shop URLs are copied from public shop pages so we can display and alert on them. That is shop catalogue data, not your personal account data.</li>
<li><strong>Messaging platforms.</strong> If you follow or join our Threads, Telegram, or Discord, those platforms process your account under their policies. We do not get your password. We only use our own bot/app tokens to post public stock messages.</li>
</ul>
<h2>How we use it</h2>
<p>We use the data above to run the stock dashboard, measure whether the site is useful, and publish stock alerts. We do not sell personal data. We do not use the Threads API to build advertising profiles of followers.</p>
<h2>Sharing</h2>
<p>Hosting and CDN providers (including Cloudflare) may process request logs. Google processes Analytics. Meta processes Threads API calls when we post. Telegram and Discord process messages in those channels. We do not sell lists of users.</p>
<h2>Retention</h2>
<p>Stock history is kept so the website can show recent in-stock changes. Analytics retention follows Google Analytics settings.</p>
<h2>Your choices</h2>
<p>You can block cookies or Analytics in your browser, unfollow or leave the alert channels, or stop using the site. To ask a question about this policy, open <a href="https://hkbeybladex.com">https://hkbeybladex.com</a> or message the HK BeybladeX Watch Threads profile linked from the subscribe page.</p>
<h2>私隱政策（中文摘要）</h2>
<p>本網站提供香港爆旋陀螺舖頭貨況同到貨通知。我們會用 Google Analytics 了解瀏覽情況。我們唔會出售你嘅個人資料。Discord、Telegram、Threads 帳戶由該平台處理。查詢請到本網站或 Threads 專頁。</p>
<p><a href="/terms">Terms of Service</a></p>
</body>
</html>`;

const TERMS = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Terms of Service · HK BeybladeX Watch</title>
<meta name="description" content="Terms of service for HK BeybladeX Watch stock dashboard and optional Threads / Telegram / Discord alerts.">
<link rel="canonical" href="https://hkbeybladex.com/terms">
</head>
<body>
<h1>Terms of Service</h1>
<p>Last updated: 1 September 2026</p>
<p>These terms apply to <a href="https://hkbeybladex.com">https://hkbeybladex.com</a> and the related Threads, Telegram, and Discord stock-alert channels operated as HK BeybladeX Watch. The project is unofficial and not affiliated with Takara Tomy, Hasbro, or the shops we watch.</p>
<h2>The service</h2>
<p>We show public Hong Kong hobby-shop Beyblade X stock information and may post optional alerts. Stock, prices, and availability can be wrong, delayed, or incomplete. Listings are not an offer to sell. Buy only from the shop’s own website.</p>
<h2>Acceptable use</h2>
<ul>
<li>Use the site and alert channels for personal, non-commercial stock watching.</li>
<li>Do not abuse, overload, or attempt to disrupt the site, alerts, or shop websites through this service.</li>
<li>Do not use the service to impersonate shops, claim official affiliation, or mislead others about stock.</li>
</ul>
<h2>Alerts and third-party platforms</h2>
<p>Threads, Telegram, Discord, Google Analytics, Cloudflare, and shop websites are third-party services. Their own terms apply when you use them. We do not control shop checkout, payment, or fulfilment.</p>
<h2>No warranty</h2>
<p>The service is provided free, as is, with no guarantee that it will stay online, stay accurate, or continue posting alerts. We may change or stop any part of it at any time.</p>
<h2>Limitation of liability</h2>
<p>To the extent allowed by law, we are not liable for missed restocks, incorrect listings, missed alerts, or any purchase you make (or fail to make) because of this site or its channels.</p>
<h2>Privacy</h2>
<p>How we handle analytics, cookies, and platform data is described in the <a href="/privacy">Privacy Policy</a>.</p>
<h2>Contact</h2>
<p>Questions about these terms: open <a href="https://hkbeybladex.com">https://hkbeybladex.com</a> or message the HK BeybladeX Watch Threads profile linked from the subscribe page.</p>
<h2>服務條款（中文摘要）</h2>
<p>本網站同相關通知頻道係非官方嘅香港爆旋陀螺貨況工具，與 Takara Tomy、Hasbro 及各舖頭無關。貨況可能有錯或延遲，並非售賣要約。請只喺舖頭官方網站購買。服務免費、無保證，我們可以隨時更改或停止。詳情見英文條款同<a href="/privacy">私隱政策</a>。</p>
</body>
</html>`;

export default {
  async fetch(request) {
    const path = new URL(request.url).pathname.replace(/\/+$/, "") || "/";
    const pages = {
      "/privacy": HTML,
      "/privacy-policy": HTML,
      "/terms": TERMS,
      "/terms-of-service": TERMS,
    };
    const body = pages[path];
    if (!body) return new Response("Not found", { status: 404 });
    return new Response(request.method === "HEAD" ? null : body, {
      status: 200,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=300",
        "x-robots-tag": "index, follow",
      },
    });
  },
};
