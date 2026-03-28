## 2026-03-28 - Removed `os.system("")` hack
**Vulnerability:** Use of `os.system("")` to enable ANSI escape codes on Windows.
**Learning:** This approach executes an empty string as a system command, which is an unnecessary attack vector and generally an anti-pattern (especially since it relies on system shell evaluation and can be hijacked if the environment path is manipulated or shell variables are overridden). The standard Win32 API provides `ctypes.windll.kernel32.SetConsoleMode` to enable terminal processing securely without spawning a subshell.
**Prevention:** Avoid `os.system()` and use platform-specific APIs (like `ctypes` on Windows) for low-level console state changes, or rely on a vetted library like `colorama`.
