## 2025-02-23 - [Missing Foundational Security Headers]
**Vulnerability:** The Flask application lacked foundational security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`), exposing it to clickjacking, MIME-type sniffing, and unintended cross-origin referrer leakage.
**Learning:** This gap existed because these headers were not applied globally as part of the application factory pattern, and CSP was specifically omitted per repository guidelines without replacing it with adequate alternative headers.
**Prevention:** Always implement an `after_request` hook (or use a library like Flask-Talisman, if not otherwise restricted) to enforce baseline security headers defensively on all responses.
