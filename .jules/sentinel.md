## 2025-03-08 - Added Global HTTP Security Headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

**Vulnerability:** The application was missing basic defense-in-depth HTTP security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** These standard headers were absent, leaving the app vulnerable to clickjacking and MIME-sniffing. A previous attempt to add `Content-Security-Policy` via Flask-Talisman (Batch 17 WP-5) was abandoned because it broke inline styles required by the templates.
**Prevention:** Rather than using a third-party extension like Flask-Talisman, standard security headers can be globally applied via a simple `@application.after_request` hook, avoiding the complexities and breakages associated with overly strict Content-Security-Policies while still applying essential protections.
