import os

from src.config import *
from src.constants import *
from src.helpers import *

def init_ctx(ctx:dict, file:str, flags:list):
    if "force-pkgbuild" in flags:
        ctx["type"] = "pkgbuild"
    else:
        if file == "PKGBUILD":
            ctx["type"] = "pkgbuild"
        else:
            # Guess NFX Package
            ctx["type"] = "nfxbuild"

    if "force-srcinfo" in flags:
        ctx["build_type"] = "srcinfo"
    else:
        ctx["build_type"] = "pkginfo.nfx"

    if ctx["type"] == "pkgbuild":
        ctx["shell"] = "bash"
    else:
        ctx["shell"] = "ash"

def parse_string(ctx: dict, s: str) -> Union[str, bool]:
    if not s.startswith("\"") and not s.startswith("'"): return False

    if (s.startswith("\"") and not s.endswith("\"")) or (not s.startswith("\"") and s.endswith("\"")):
        eerror(f"Line {ctx["lineno"]} : Please Start/Close String (Incorrect String)")
    elif (s.startswith("'") and not s.endswith("'")) or (not s.startswith("'") and s.endswith("'")):
        eerror(f"Line {ctx["lineno"]} : Please Start/Close String (Incorrect String)")
    
    f = s.removesuffix("\"").removeprefix("\"").removesuffix("'").removeprefix("'")
    return f

def parse_array(ctx: dict, arr:str) -> Union[list, bool]:
    if not arr.startswith("("): return False
    
    if (arr.startswith("(") and not arr.endswith(")")) or (not arr.startswith("(") and arr.endswith(")")):
        eerror(f"Line {ctx["lineno"]} : Please Start/Close Array (Incorrect Array)")
    a = arr.removeprefix("(").removesuffix(")")
    items = a.split(",")
    final = []
    for item in items:
        final.append(parse_string(ctx, item))
    return final

def parse_pkgbuild(ctx: dict, file:str):
    with open(file, "r") as f:
        f.seek(0)
        ctx["data"] = f.read()
    
    data = ctx["data"]
    lines = data.splitlines()
    for lineno, line in enumerate(lines):
        ctx["lineno"] = lineno
        nl = "".join(line.split())
        if "=" in nl:
            key, val = nl.split("=", 1)
            if key == "pkgbase":
                if val.startswith("(") and val.endswith(")"):
                    arr = parse_array(ctx, val)
                    if len(arr) < 1 or arr[0] == "":
                        eerror(f"Line {lineno} : Empty Array Cannot be used")
                    ctx["name"] = arr[0]
                else:
                    ctx["name"] = val
                step(f"Package Base: {ctx["name"]}", "Log")
            elif key == "pkgname":
                if ctx["name"] == "": ctx["name"] = val

def pkg_build(args:list, flags:list, config: Config) -> None:
    """Makes Packages"""
    file = args[0]
    ctx = {
        "type": "nfxbuild",
        "build_type": "pkginfo.nfx",
        "shell": "ash",
        "flags": flags,
        "config": config,
        "name": "",
        "split-names": [],
        "data": "",
        "lineno": 0
    }

    init_ctx(ctx, file, flags)

    # Parse
    if ctx["type"] == "pkgbuild":
        new_item("Building PKGBUILD")
        parse_pkgbuild(ctx, file)
