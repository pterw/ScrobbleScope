## 2024-03-16 - Add Standard Security Headers
**Vulnerability:** Missing standard HTTP security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** Default Flask application does not set secure HTTP headers, leaving the application vulnerable to clickjacking and MIME-type sniffing.
**Prevention:** Always implement an `@application.after_request` hook to set baseline security headers for all responses.
