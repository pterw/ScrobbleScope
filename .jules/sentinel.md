## 2024-05-18 - Missing Security Headers

**Vulnerability:** The application was missing standard HTTP security headers globally. Specifically, `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy` were missing, which could lead to clickjacking, MIME-type sniffing, and cross-origin referrer leakage.

**Learning:** Although CSRF protection was in place (Flask-WTF), other common defense-in-depth headers had not been globally applied to the Flask application.

**Prevention:** Ensure that new Flask applications establish an `after_request` hook (or use a library like Flask-Talisman, though omitted here to avoid breaking inline styles with CSP) to inject these defense-in-depth security headers at the framework level.