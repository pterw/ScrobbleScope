## 2024-05-18 - [Insecure OS Command Usage for Console Formatting]
**Vulnerability:** Use of `os.system("")` hack to enable ANSI escape codes on Windows.
**Learning:** `os.system()` relies on the system shell, introducing a risk of command injection if arguments are ever dynamically formatted or influenced by untrusted input, and generally exposes the application to unnecessary shell execution. Even with an empty string, executing system shells is bad practice.
**Prevention:** Use direct Win32 API calls (`ctypes.windll.kernel32.SetConsoleMode`) instead of shell-based hacks to achieve console formatting effects on Windows.
