## 2026-03-07 - Add Global HTTP Security Response Headers
**Vulnerability:** Missing security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) could leave the application vulnerable to Clickjacking and MIME-type sniffing attacks.
**Learning:** These headers weren't defined in the Flask application factory. This is a common gap for Flask applications, relying on a reverse proxy to set these headers when they should be set by the application itself as defense in depth.
**Prevention:** Ensured the headers are set globally on all responses using an `@application.after_request` hook in `app.py`. Next time verify standard security headers exist out-of-the-box or define them initially.
