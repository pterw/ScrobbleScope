## 2026-03-21 - Command Injection Risk in Console Formatting
**Vulnerability:** Found `os.system("")` used as a hack to enable ANSI escape codes in Windows terminals. This passes untrusted or empty commands to the shell.
**Learning:** This existed because it's a common, copy-pasted hack to force `cmd.exe` to interpret ANSI colors, but it technically invokes a subshell unnecessarily and poses a risk if modified.
**Prevention:** Use direct Win32 API calls (`ctypes.windll.kernel32.SetConsoleMode`) instead of `os.system()` to interact with the OS environment securely.
