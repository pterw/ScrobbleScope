## 2024-03-24 - Removing os.system hack for enabling ANSI escape codes
**Vulnerability:** Execution of an empty command via `os.system("")`
**Learning:** This is a common but dangerous hack to enable ANSI escape codes in Windows Command Prompt, but introduces unnecessary execution of shell processes that could be risky and are poor practice. The safer alternative is explicitly using Win32 API calls via `ctypes`.
**Prevention:** Rather than executing generic shell commands simply for their side effects, make use of direct API calls, such as `ctypes.windll.kernel32.SetConsoleMode`.
