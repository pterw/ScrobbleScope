## 2026-03-23 - Missing Default Security Headers
**Vulnerability:** ScrobbleScope was sending responses without standard HTTP security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy), leaving it susceptible to clickjacking, MIME-sniffing, and referrer leakage.
**Learning:** Frameworks like Flask do not configure these baseline headers by default. Even when advanced headers like CSP are explicitly opted-out or deemed unnecessary for a given context, fundamental security headers should still be explicitly applied via application-wide request hooks (e.g., `@after_request`).
**Prevention:** Implement a global `@after_request` hook in the application factory to ensure security headers are automatically attached to all outbound responses, including error pages (e.g., 404s).
