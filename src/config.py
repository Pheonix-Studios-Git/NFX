"""Handles Config and more"""
import os
import json
from dataclasses import dataclass
from typing import Optional

from constants import CACHE_DIR_DEF, CONFIG_PATH_DEF, INSTALL_DIR_DEF, DOWNLOAD_DIR_DEF

@dataclass
class Config:
    """Config Class"""
    cache_dir: str = CACHE_DIR_DEF
    install_dir: str = INSTALL_DIR_DEF
    download_dir: str = DOWNLOAD_DIR_DEF
    debug: bool = False
    default_repos: list[str] = None

    @staticmethod
    def load(path:str=CONFIG_PATH_DEF):
        """Loads the config"""
        if not os.path.exists(path):
            return Config(default_repos=[])
        with open(path, "r") as f:
            data = json.load(f)
        return Config(
            cache_dir=data.get("cache_dir", CACHE_DIR_DEF), 
            debug=data.get("debug", False), 
            default_repos=data.get("default_repos", []), 
            install_dir=data.get("install_dir", INSTALL_DIR_DEF),
            download_dir=data.get("download_dir", DOWNLOAD_DIR_DEF)
        )

    def save(self, path:str=CONFIG_PATH_DEF):
        """Saves the config"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=4)
