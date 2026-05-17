import os

from src.config import *
from src.constants import *
from src.helpers import *

def init_ctx(ctx:dict, file:str, flags:list):
    if "force-pkgbuild" in flags:
        ctx["type"] = "pkgbuild"
    else:
        if "PKGBUILD" in file:
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

class PKGBUILDer:
    def __init__(self, ctx: dict, file: str):
        self.ctx = ctx
        self.file = file
        self.skip_lines = 0
        with open(self.file, "r") as f:
            f.seek(0)
            self.ctx["data"] = f.read()

        self.vars: dict[str, tuple[str, list[str], str]] = {
            "pkgbase": ("name", ["string"], "string"),
            "pkgver": ("version", ["string"], "string"),
            "pkgrel": ("release-version", ["string"], "string"),
            "pkgdesc": ("description", ["string"], "string"),
            "pkgname": ("split-names", ["list", "string"], "list"),

            "url": ("site-url", ["string"], "string"),
            "builddate": ("build-date", ["string"], "string"),
            "packager": ("packager-id", ["string"], "string"),
            "size": ("package-size", ["int"], "int"),
            "arch": ("arch", ["list"], "list"),
            "license": ("license", ["list"], "list"),
            "group": ("groups", ["list"], "list"),

            "backup": ("backup-files", ["list"], "list"),

            "depends": ("depends", ["list"], "list"),
            "makedepends": ("make-depends", ["list"], "list"),
            "checkdepends": ("check-depends", ["list"], "list"),
            "optdepends": ("optional-depends", ["list"], "list"),

            "provides": ("provides", ["list"], "list"),
            "conflicts": ("conflicts", ["list"], "list"),
            "replaces": ("replaces", ["list"], "list"),

            "source": ("sources", ["list"], "list"),
            "noextract": ("no-extract-files", ["list"], "list"),

            "validpgpkeys": ("valid-pgp-keys", ["list"], "list"),

            "md5sums": ("md5sums", ["list"], "list"),
            "sha1sums": ("sha1sums", ["list"], "list"),
            "sha512sums": ("sha512sums", ["list"], "list"),
            "sha384sums": ("sha384sums", ["list"], "list"),
            "sha256sums": ("sha256sums", ["list"], "list"),
            "sha224sums": ("sha224sums", ["list"], "list"),

            "epoch": ("epoch", ["int"], "int"),
        }
        self.local_vars: dict[str, tuple[str, str]] = {}

    def _type_of_v(self, s: str) -> str:
        if s.startswith("\"") or s.startswith("'"): return "string"
        elif s.startswith("("): return "list"
        return "string"

    def _parse_string(self, s: str) -> Union[str, bool]:
        f = ""
        within_quotes = False
        within_var = False
        check_var = False
        escaped = False

        var = ""

        for i, c in enumerate(s):
            if not escaped:
                if within_quotes and i >= len(s):
                    error(f"[Line {self.ctx['lineno']}] Unterminated quotes!")
                    return False
                elif within_var:
                    if check_var:
                        if c == '{':
                            check_var = False
                            continue
                        else:
                            f += c
                            continue
                    if c == '}':
                        within_var = False
                        check_var = False
                        if var != "":
                            if var not in self.local_vars:
                                error(f"[Line {self.ctx['lineno']}] Unknown variable '{var}'")
                                return False
                            val, typ = self.local_vars[var]
                            if typ == "string":
                                f += val
                            elif typ == "int":
                                f += str(val)
                            elif typ == "list":
                                f += str(val)
                        var = ""
                        continue
                    var += c
                    continue

                if c == '\\':
                    escaped = True
                    continue
                elif c in ('"', '\''):
                    within_quotes = not within_quotes
                    continue
                elif c == '#':
                    break
                elif c == '$':
                    within_var = True
                    check_var = True
                    continue
                f += c
            else:
                escaped = False
                if c == '\\':
                    if not within_quotes:
                        pass # TODO: Add multiline support
                    f += c
                    continue
                elif c == 'n':
                    f += '\n'
                    continue
                elif c in ('"', '\''):
                    f += c
                    continue
                f += '\\' + c
        
        return f

    def _parse_array(self, arr:str) -> Union[list, bool]:
        if not arr.startswith("("): return False
        
        items = []
        found_end = False
        found_start = False
        got_comma = False
        in_string = False
        ckd_lines = 0
        lines:list[str] = self.ctx["data"].splitlines()[self.ctx["lineno"]-1:]
        while not found_end and ckd_lines < len(lines):
            v = ""
            line = lines[ckd_lines].strip()
            escaped = False
            for c in line:
                if found_start and got_comma:
                    if c in (' ', '\t'): continue
                    got_comma = False
                    
                if not escaped:
                    if c == '\\' and found_start:
                        escaped = True
                        continue
                    elif c == '#' and not in_string:
                        break; # next line
                    elif c == '(':
                        found_start = True
                        continue
                    elif (c == ',' or c == ' ') and not in_string and found_start:
                        got_comma = True
                        if v != "": items.append(v.strip())
                        continue
                    elif c == ')' and found_start:
                        if not found_start: continue
                        found_end = True
                        break
                    elif c in ('"', '\'') and found_start:
                        in_string = not in_string
                        continue
                elif escaped and found_start:
                    escaped = False
                    if c == '\\':
                        v += c
                        continue
                    elif c == 'n':
                        v += '\n'
                        continue
                    elif c in ('\'', '"'):
                        v += c
                        continue
                    else:
                        v += '\\' + c # like bash
                        continue

                if found_start: v += c
            if v != "": items.append(v.strip())
            v = ""
            ckd_lines += 1

        if ckd_lines > 1:
            self.skip_lines = ckd_lines - 1

        final = []
        for item in items:
            final.append(self._parse_string(item))
        return final

    def parse(self) -> bool:
        data:str = self.ctx["data"]
        lines = data.splitlines()
        for lineno_raw, line in enumerate(lines):
            line = line.strip()
            _in_string = False
            _escaped = False
            for i, c in enumerate(line): # Remove comments
                if not _escaped:
                    if c in ('\'', '"'):
                        _in_string = not _in_string
                        continue
                    elif c == '#' and not _in_string:
                        line = line[:i]
                        break
                    elif c == '\\':
                        escaped = True
                        continue
                else:
                    escaped = False # We dont need extra code here
            
            lineno = lineno_raw + 1
            self.ctx["lineno"] = lineno

            if self.skip_lines > 0:
                self.skip_lines -= 1
                continue

            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip(" \t\r")
                typ = self._type_of_v(val)
                
                if key in self.vars:
                    ctx_key, allowed_types, target_type = self.vars[key]

                    if typ not in allowed_types:
                        error(f"[Line {lineno}] Invalid type of value used (can be {", ".join(allowed_types)} | got {typ})")
                        return False
                    
                    if typ == "list":
                        a = self._parse_array(val)
                        if a is False: return False
                        if target_type == "list":
                            self.ctx[ctx_key] = a
                        elif target_type == "string":
                            self.ctx[ctx_key] = a[0]
                        elif target_type == "int":
                            v = a[0]
                            if v.isidigit():
                                self.ctx[ctx_key] = int(v)

                        self.local_vars[key] = (a, "list")
                    elif typ == "string":
                        s = self._parse_string(val)
                        if s is False: return False
                        if target_type == "list":
                            self.ctx[ctx_key] = [s]
                        elif target_type == "string":
                            self.ctx[ctx_key] = s
                        elif target_type == "int":
                            if s.isidigit():
                                self.ctx[ctx_key] = int(s)

                        self.local_vars[key] = (s, "string")
                    elif typ == "int":
                        s = self._parse_string(val)
                        if s is False: return False

                        if not s.isdigit():
                            error(f"[Line {lineno}] Invalid type of value used (Needs int)")
                            return False
                        if target_type == "list":
                            self.ctx[ctx_key] = [s]
                        elif target_type == "string":
                            self.ctx[ctx_key] = s
                        elif target_type == "int":
                            self.ctx[ctx_key] = int(s)

                        self.local_vars[key] = (s, "int")

        return True

def emit_srcinfo(ctx: dict) -> str:
    err = False
    out = []

    if ctx["name"] == "":
        if len(ctx["split-names"]) <= 0:
            error("Package Name never specified!")
            return None
        ctx["name"] = ctx["split-names"][0]
    out.append(f"pkgbase = {ctx['name']}")

    def emit(key, v, required=False):
        nonlocal err
        if v is None or v == "" or v == []:
            if required:
                error(f"Required field {key} missing!")
                err = True
            return

        if isinstance(v, list):
            for i in v:
                out.append(f"\t{key} = {i}")
        else:
            out.append(f"\t{key} = {v}")

    emit("pkgver", ctx["version"], required=True)
    emit("pkgrel", ctx["release-version"] or 1, required=True)

    emit("epoch", ctx["epoch"])

    emit("pkgdesc", ctx["description"])
    emit("url", ctx["site-url"])

    emit("arch", ctx["arch"])
    emit("license", ctx["license"])
    emit("group", ctx["groups"])

    emit("builddate", ctx["build-date"])
    emit("packager", ctx["packager-id"])
    emit("size", ctx["package-size"])

    emit("depends", ctx["depends"])
    emit("makedepends", ctx["make-depends"])
    emit("checkdepends", ctx["check-depends"])
    emit("optdepends", ctx["optional-depends"])

    emit("provides", ctx["provides"])
    emit("conflicts", ctx["conflicts"])
    emit("replaces", ctx["replaces"])

    emit("options", ctx["options"] if ctx["options"] != [] else "!strip")

    emit("source", ctx["sources"])
    emit("noextract", ctx["no-extract-files"])

    emit("validpgpkeys", ctx["valid-pgp-keys"])

    emit("md5sums", ctx["md5sums"])
    emit("sha1sums", ctx["sha1sums"])
    emit("sha512sums", ctx["sha512sums"])
    emit("sha384sums", ctx["sha384sums"])
    emit("sha256sums", ctx["sha256sums"])
    emit("sha224sums", ctx["sha224sums"])

    for name in ctx["split-names"]:
        out.append("")
        out.append(f"pkgname = {name}")

    return "\n".join(out) if not err else None

def pkg_build(args:list, flags:list, config: Config) -> None:
    """Makes Packages"""
    file = args[0]
    ctx = {
        "type": "nfxbuild",
        "build_type": "pkginfo.nfx",
        "shell": "ash",
        "flags": flags,
        "config": config,

        "lineno": 0,
        "data": "",

        "name": "",
        "split-names": [],
        "version": "",
        "release-version": "",
        "epoch": None,
        "description": "",

        "build-date": "",
        "packager-id": "",
        "package-size": None,

        "arch": ["any"],

        "site-url": "",
        "license": [],

        "groups": [],

        "arch-depends": {},
        "depends": [],
        "make-depends": [],
        "check-depends": [],
        "optional-depends": [],

        "provides": [],
        "conflicts": [],
        "replaces": [],

        "backup-files": [],
        "options": [],
        "install": "",
        "changelog": "",

        "sources": [],
        "no-extract-files": [],

        "valid-pgp-keys": [],

        "b2sums": [],
        "sha512sums": [],
        "sha384sums": [],
        "sha256sums": [],
        "sha224sums": [],
        "sha1sums": [],
        "md5sums": [],
        "cksums": [],
    }

    out = ""
    for flg in flags:
        if "out-build=" in flg:
            out = flg.replace("out-build=", "")
            break

    new_item("Building Package")

    jump("Initializing Info")
    init_ctx(ctx, file, flags)

    # Parse
    jump("Parsing")
    if ctx["type"] == "pkgbuild":
        new_item("Building - PKGBUILD")
        builder = PKGBUILDer(ctx, file)
        if not builder.parse():
            error("Package Build Failed")
            return None

    new_item(f"Writing BUILD to {'stdout' if out == '' else out}")
    infod = emit_srcinfo(ctx) if ctx["build_type"] == "srcinfo" else None
    if out is None: return None
    if out == "": print(f"\n{infod}\n")
    else:
        with open(out, "w") as f:
            f.write(infod)

    new_item("Finishing")
    step("Build Completed", color="green", bold=True)
