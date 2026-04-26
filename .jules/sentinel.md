## 2026-04-26 - Missing Global Security Headers
**Vulnerability:** The application lacks standard HTTP security headers such as `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`, leaving it vulnerable to clickjacking and MIME-type sniffing.
**Learning:** These basic security headers were previously missing because the `create_app` factory in `app.py` did not implement an `@application.after_request` hook. Flask does not add these by default.
**Prevention:** Always implement standard security headers either via a reverse proxy (like Nginx) or via Flask global hooks in the application factory to ensure a baseline level of defense.
