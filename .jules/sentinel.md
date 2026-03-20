## 2026-03-20 - Insecure os.system call
**Vulnerability:** A vulnerable `os.system("")` call was used to enable ANSI escape codes on Windows cmd. This can lead to security risks if not carefully managed or if a shell is compromised.
**Learning:** Legacy or shortcut code snippets often persist without consideration for their broader security implications. The `os.system("")` trick is widely copied but inherently uses the shell.
**Prevention:** Avoid `os.system` entirely. Always use secure alternatives like `subprocess` or direct Win32 API calls (`ctypes.windll.kernel32.SetConsoleMode`) when interacting with the OS.

## 2026-03-20 - Missing Global HTTP Security Headers
**Vulnerability:** The application was not setting standard HTTP security headers globally (e.g., `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`), which could expose it to clickjacking, MIME-type sniffing, and potentially sensitive data leakage through referrers.
**Learning:** Security headers are easily overlooked but are a fundamental layer of defense. They should be applied uniformly across all endpoints rather than relying on individual route configurations.
**Prevention:** Use a global `@application.after_request` hook or middleware (like Flask-Talisman) to ensure all responses automatically include essential security headers, adhering to the principle of "secure by default".