"""Nova Pheonix Package Manager"""

import platform

def get_system_info():
    os_name = platform.system().lower() # 'linux', 'windows', 'darwin'
    if os_name == "darwin":
        os_name = "macos"
    arch = platform.machine().lower() # 'x86_64', 'arm64', etc.
    if arch in ["amd64", "x86_64"]:
        arch = "x86_64"
    elif arch in ["i386", "i686", "x86"]:
        arch = "x86"
    return os_name, arch
