## 2026-03-13 - HTTP Security Headers Added Manually
**Vulnerability:** Missing basic HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) because Flask-Talisman was dropped due to CSP incompatibility with inline styles.
**Learning:** Dropping a security library (Flask-Talisman) due to one incompatible feature (CSP breaking inline styles) shouldn't result in abandoning the other independent security benefits (like basic HTTP headers). It is important to implement what is feasible manually if a library approach is rejected.
**Prevention:** Evaluate the individual security features provided by a library and implement the compatible ones manually if the entire library cannot be used.
