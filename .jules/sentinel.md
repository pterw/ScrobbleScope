## 2026-03-05 - Add Security Headers
**Vulnerability:** Missing standard security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
**Learning:** The application was missing basic defense-in-depth headers, making it slightly more susceptible to Clickjacking and MIME-sniffing.
**Prevention:** In Flask apps, always add an `@app.after_request` hook to inject standard security headers.
