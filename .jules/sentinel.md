## 2024-05-24 - [Add Global HTTP Security Response Headers]
**Vulnerability:** The application was not transmitting standard HTTP security response headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`), potentially enabling client-side attacks like clickjacking and MIME-type sniffing.
**Learning:** Found that basic HTTP security enhancements were overlooked, likely due to focusing heavily on API keys and CSRF protection.
**Prevention:** Implement a standard setup for HTTP security headers globally on all web frameworks, utilizing a dedicated response handler like `@application.after_request` in Flask, before deploying to production.
