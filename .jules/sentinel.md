## 2024-05-14 - Fix Command Injection Risk in Console Configuration
**Vulnerability:** Command injection risk via `os.system("")` used to enable ANSI escape codes on Windows.
**Learning:** `os.system()` executes the given command in a subshell. Even when passing an empty string (`""`), spawning a subshell can be risky and is considered a poor practice for simple system configurations. It bypasses the safety of standard APIs and could theoretically be hooked or exploited if `cmd.exe` or environment variables are tampered with.
**Prevention:** Use direct, secure API calls like `ctypes.windll.kernel32.SetConsoleMode()` to configure the console instead of relying on side effects of subshell execution.
