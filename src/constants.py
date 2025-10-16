"""Constants"""

import os

VERSION = "0.1.0"
DEVELOPER = "Pheonix Studios"

SEPERATORS = [":", ";", "->", "-", "="]

CONFIG_PATH_DEF = os.path.expanduser("~/.config/nfx/config.json")

BASE_DIR_DEF = os.path.expanduser("~/.nfx")
INSTALL_DIR_DEF = os.path.join(BASE_DIR_DEF, "installs")
CACHE_DIR_DEF = os.path.join(BASE_DIR_DEF, "cache")
DOWNLOAD_DIR_DEF = os.path.join(BASE_DIR_DEF, "downloads")
