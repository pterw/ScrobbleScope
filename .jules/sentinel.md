## 2026-03-15 - Missing Global Security Headers
**Vulnerability:** The application was missing standard HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) globally across all routes.
**Learning:** Security headers must be explicitly configured globally to provide baseline protection against clickjacking, MIME-type sniffing, and sensitive data leakage via Referrer headers. They should apply even to error pages (like 404s).
**Prevention:** Apply a global `@application.after_request` hook in the main application factory (`app.py`) to ensure every outgoing response is secured by default.
