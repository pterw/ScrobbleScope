## 2025-02-28 - Insecure `os.system("")` Usage
**Vulnerability:** Found `os.system("")` used to enable ANSI escape codes on Windows consoles in `app.py`.
**Learning:** Using `os.system()` invokes a subshell and is considered bad practice when better APIs exist. It also unnecessarily runs a shell on non-Windows systems where it isn't needed.
**Prevention:** Use direct Win32 APIs like `ctypes.windll.kernel32.SetConsoleMode` to enable ANSI escape sequences securely without shelling out, and wrap the call in an `os.name == "nt"` check.
