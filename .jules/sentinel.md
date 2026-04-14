## 2026-04-14 - Application HTTP Security Headers Enhancement
**Vulnerability:** The application was missing basic defense-in-depth HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) globally across responses.
**Learning:** Standard security headers should be enforced globally using application hooks (like Flask's `after_request`) instead of relying on specific route configuration.
**Prevention:** In the future, ensure global security policies are centralized in the application factory configuration. Note that CSP was explicitly omitted per project policy (YAGNI / Batch 17 WP-5).
