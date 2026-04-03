## 2025-02-28 - Command Injection Risk via os.system("")
**Vulnerability:** A bare `os.system("")` call was used to enable ANSI escape codes on Windows cmd terminals.
**Learning:** `os.system` invokes a subshell, which is inefficient and introduces a potential attack surface for command injection if any unintended environment modification occurs. The subshell execution itself can be dangerous in constrained or monitored environments.
**Prevention:** Use direct system API calls instead of shelling out. For Windows terminal modifications, use `ctypes.windll.kernel32.SetConsoleMode` directly instead of relying on the undocumented side-effect of `os.system("")`.
