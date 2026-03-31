## 2024-05-14 - Subshell Execution for Console Configuration
**Vulnerability:** Found `os.system("")` used as a hack to enable ANSI escape codes in Windows cmd. This unnecessarily executes a subshell and creates an opening for command injection or unintended OS interactions if not carefully isolated.
**Learning:** Avoid using side-effects of system commands for configuration tasks that can be achieved via direct API calls. `os.system()` should only be used as a last resort when direct execution/API access is impossible, and never just for side effects like terminal initialization.
**Prevention:** Use direct OS API bindings like `ctypes.windll.kernel32.SetConsoleMode` on Windows to configure console properties securely without spawning sub-processes.
