## 2025-04-11 - Global Security Headers Added via App Factory
**Vulnerability:** Missing standard HTTP security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** The application was missing basic defense-in-depth protections against clickjacking and MIME-sniffing, primarily because these headers weren't set globally on the Flask app factory.
**Prevention:** Ensured an `@application.after_request` hook is registered in `create_app` in `app.py` to automatically inject these headers into all outgoing HTTP responses.
