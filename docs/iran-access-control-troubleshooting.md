# Browser loading failures + Iran-only access hardening

This guide covers:
1. Why a site loads in one browser/network and fails in another.
2. How to diagnose DNS/server/regional restrictions.
3. How to make access available **only** to users from Iran, while keeping good performance.

## 1) Common reasons a website link fails in some browsers

### DNS and hostname resolution
- `A`/`AAAA` records missing, stale, or inconsistent between DNS resolvers.
- Domain has only IPv6 (`AAAA`) but origin/network path does not support IPv6 end-to-end.
- Split-horizon DNS (internal vs public DNS mismatch).

### TLS / HTTPS issues
- TLS certificate CN/SAN mismatch with requested host.
- Incomplete certificate chain (some browsers fail harder than others).
- Old TLS versions/cipher suites disabled incompatibly.
- HSTS previously cached for domain while site is temporarily served via HTTP.

### Browser-specific client behavior
- Strict tracking protection or mixed-content blocking (HTTP asset on HTTPS page).
- Legacy cache/service-worker delivering stale assets.
- CSP/CORS headers blocking frontend API calls in some contexts.

### Server and reverse-proxy misconfiguration
- Wrong `Host` routing in Nginx/Apache (default vhost catches the request).
- Upstream timeout/502/504 for dynamic endpoints.
- Redirect loops between `http` and `https` or between `www` and apex domain.

### Regional/network restrictions
- CDN/WAF geo-rules deny specific regions.
- ISP filtering or DNS poisoning.
- GeoIP database out of date, misclassifying Iranian IP blocks.

## 2) Recommended diagnostic sequence

1. **DNS checks** (`dig`, `nslookup`) from multiple resolvers (local ISP, 1.1.1.1, 8.8.8.8).
2. **HTTP/TLS checks** (`curl -Iv https://domain`, SSL Labs, certificate chain).
3. **Proxy logs** (Nginx/Apache access + error logs by status code, host, user-agent, country header).
4. **Application logs** for 4xx/5xx and response latency.
5. **Browser devtools** network tab for blocked scripts/CORS/mixed content.

## 3) Iran-only access design (recommended)

Use a layered model:
- **Edge layer (CDN/WAF/Nginx)**: primary geo restriction by country code (`IR`).
- **Application layer (FastAPI middleware)**: secondary deny rule if edge headers are missing/spoofed.
- **Firewall layer**: optional hard network controls for high-security deployments.

### Why layered
- Fast rejection at edge improves performance.
- App-level check gives defense-in-depth and clear observability.
- Firewall reduces accidental origin exposure.

## 4) FastAPI support added in this repository

The app now supports optional geo/browser restrictions using env vars:
- `GEO_RESTRICTION_ENABLED` (default `false`)
- `GEO_ALLOW_IRAN_ONLY` (default `true`)
- `ENFORCE_BROWSER_ONLY` (default `true`)
- `TRUSTED_COUNTRY_HEADER` (default `CF-IPCountry`)

When enabled, requests are denied with `403` if:
- the request does not look like a browser `User-Agent` (when `ENFORCE_BROWSER_ONLY=true`), or
- the trusted country header is not `IR`.

> Important: only trust country headers injected by your own reverse-proxy/CDN, never direct internet clients.

## 5) Nginx sample (preferred geo enforcement)

```nginx
# If using Cloudflare, CF-IPCountry is set at edge.
map $http_cf_ipcountry $allow_country {
    default 0;
    IR 1;
}

server {
    listen 443 ssl;
    server_name example.com;

    if ($allow_country = 0) {
        return 403;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header CF-IPCountry $http_cf_ipcountry;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## 6) Apache/.htaccess sample

```apache
RewriteEngine On
# Requires country code passed by edge/proxy, e.g. CF-IPCountry
RewriteCond %{HTTP:CF-IPCountry} !^IR$ [NC]
RewriteRule ^ - [F,L]
```

If you run pure Apache without trusted edge headers, prefer `mod_maxminddb` and deny non-IR at vhost level.

## 7) Firewall strategy (optional, high security)

- Keep origin server private; allow ingress only from CDN/WAF IP ranges.
- If no CDN is used, update country IP ranges (Iran ASNs/CIDRs) regularly and apply allowlist rules.
- Automate updates; static manual CIDR rules quickly become stale.

## 8) Performance and UX for Iranian users

- Serve static assets via CDN PoPs with good Iran connectivity.
- Use HTTP/2/HTTP/3 and gzip/brotli.
- Cache aggressively for static resources.
- Avoid external third-party scripts blocked/slow in local networks.
- Monitor p95 latency and 403 geo-deny rates separately.