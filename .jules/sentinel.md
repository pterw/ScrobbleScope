## 2025-02-28 - Missing Security Headers

**Vulnerability:** The application was missing standard HTTP security headers: `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`.

**Learning:** Although these don't protect against direct exploitation in most APIs, they are essential defense-in-depth protections for web applications to prevent clickjacking, MIME-type sniffing, and cross-origin referrer leakage.

**Prevention:** These can be easily enforced via Flask's `@application.after_request` hook so that they are globally applied to every HTTP response without relying on per-route implementation.
