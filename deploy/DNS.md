# Cloudflare DNS (`andyhhh.com`)

Zone is full-setup on Cloudflare. Web hostnames that should hit this EC2 origin use **proxied** (orange cloud) records. Origin A is `52.77.160.129`. Do not grey-cloud those names or browsers bypass Cloudflare and can hit the box directly.

`nginx` `server_name` in `deploy/nginx-beyblade-status.conf` must list every hostname below that proxies to this origin (except Workers and unrelated vhosts).

## Required for the Beyblade site

| Type | Name | Content | Proxied | Nginx |
| --- | --- | --- | --- | --- |
| A | `andyhhh.com` | `52.77.160.129` | yes | public vhost |
| CNAME | `www.andyhhh.com` | `andyhhh.com` | yes | public vhost |
| CNAME | `beybladex-watch.andyhhh.com` | `andyhhh.com` | yes | old public name, same vhost |
| CNAME | `beybladex-admin.andyhhh.com` | `andyhhh.com` | yes | admin vhost (no cache) |
| AAAA | `beybladex-cdn.andyhhh.com` | `100::` | yes | **Worker** custom domain, not nginx |

Public site is `hkbeybladex.com`. Cache HTML there (respect origin, ~30s). Do **not** cache `beybladex-admin`.

## Also on this origin (leave alone)

| Type | Name | Notes |
| --- | --- | --- |
| A | `osaka.andyhhh.com` | Own nginx site, not the Beyblade dashboard |

Mail (`mail`, MX, SPF, SendGrid CNAMEs) stays DNS-only.

## After changing nginx

```bash
sudo cp deploy/nginx-beyblade-status.conf /etc/nginx/sites-available/beybladex-watch
# enable beybladex-watch instead of the old hobbyland-status default_server
sudo nginx -t && sudo systemctl reload nginx
```
