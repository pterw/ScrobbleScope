## 2025-02-23 - Add Missing Security Headers
**Vulnerability:** Missing standard security HTTP headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** These headers are often forgotten when initial setup is done without an explicit security layer, leaving the app vulnerable to basic clickjacking and MIME-sniffing attacks.
**Prevention:** Include a simple `@app.after_request` hook in the Flask application factory during initial scaffolding to apply fundamental security headers globally across all routes.
