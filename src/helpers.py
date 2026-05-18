import os
import subprocess

from phardwareitk.Extensions import *
from phardwareitk.Extensions.HyperOut import *
from phardwareitk.CLI import cliToolKit as cli

import urllib
from urllib.error import URLError, HTTPError, ContentTooShortError
import hashlib
import threading
from socket import timeout as stimeout
from socket import gaierror
from dataclasses import dataclass, field
import shlex

from src import get_system_info
from src.constants import *
from src.config import *
from src.errors import *

concur_pb_lock = threading.Lock()

@dataclass
class NFXRuntime:
    output: str
    inbuilt_funcs: dict[str, callable] = field(default_factory=dict)
    vars: dict = field(default_factory=dict)
    funcs: dict = field(default_factory=dict)

    def print(self, msg, status="step", color="white", bold=False):
        if self.output not in self.inbuilt_funcs:
            return None
        
        func = self.inbuilt_funcs[self.output]
        if not callable(func): return None

        msg = "" if msg is None else msg
        status = "step" if status is None else status
        color = "white" if color is None else color
        bold = False if bold is None else bold

        return func(msg, status=status, color=color, bold=bold)

    def exit(self, code=0):
        os._exit(int(code))

    def system(self, args:list):
        cOUT = self.vars["SYS_CAPTURE_OUTPUT"] == "true" if "SYS_CAPTURE_OUTPUT" in self.vars else False
        res = subprocess.run(args, capture_output=cOUT)
        self.vars["IRET"] = str(res.returncode)
        self.vars["SYS_STDOUT"] = str(res.stdout) if cOUT else ""
        self.vars["SYS_STDERR"] = str(res.stderr) if cOUT else ""

    def exists(self, files:list):
        self.vars["IRET"] = "false"
        for file in files:
            if not os.path.exists(file):
                return None
        self.vars["IRET"] = "true"

    def read(self, file:str):
        self.vars["IRET"] = ""
        if not os.path.exists(file): return None
        with open(file, "r") as f:
            f.seek(0)
            self.vars["IRET"] = str(f.read())

    def write(self, file:str, data:str):
        with open(file, "w") as f:
            f.write(data)

class NFXScriptVM:
    def __init__(self, runtime: NFXRuntime):
        self.runtime = runtime
        self.funcs_allowed = False
        self.in_comment_block = False
        self.cur_func = ""
        self.repeat_block = 0
        self.in_block = False
        self.block = ""
        self.condition = False
        self.condition_active = False

    def _parse_cmd_args(self, text: str):
        in_str=False
        s = ""
        escaped = False
        for c in text:
            if not escaped:
                if c == '\\':
                    escaped = True
                    continue
                elif c == '\"' or c == '\'':
                    in_str = not in_str
                    s += c
                    continue
                elif not in_str and c == ',':
                    s += ' '
                    continue

            if escaped:
                s += '\\'
                escaped = False
            s += c
        parts = shlex.split(s)
        cmd = parts[0] if len(parts) > 0 else ""
        _args = parts[1:] if len(parts) > 1 else []
        args = []
        for arg in _args:
            if (not ")" in arg) or (not "$(" in arg):
                args.append(arg)
                continue
            escaped = False
            checkvar = False
            invar = False
            args = []
            s = ""
            var = ""
            for c in arg:
                if not escaped:
                    if checkvar:
                        checkvar = False
                        if not c == '(':
                            s += '$' + c
                            continue
                        checkvar = False
                        invar = True
                        continue
                    elif invar:
                        if c == ')':
                            invar = False
                            val = ""
                            if not var in self.runtime.vars:
                                step(f"No such variable found, using empty : {var}", status="Warning", color="yellow", bold=True)
                            else:
                                val = str(self.runtime.vars[var])
                            s += val
                            continue
                        var += c
                        continue

                    if c == '\\':
                        escaped = True
                        continue
                    elif c == '$':
                        checkvar = True
                        continue
                else:
                    s += '\\'
                    escaped = False
                s += c
            args.append(s)

        return cmd, args

    def _parse_condition(self, text: str):
        arg, args = self._parse_cmd_args(text)
        return False # TODO: Fix

    def _handle_print(self, args):
        status = ""
        color = "white"
        bold = False
        msg = ""

        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                if k == "status":
                    status = v
                elif k == "color":
                    color = v
                elif k == "bold":
                    bold = v.lower() == "true"
            else:
                msg = arg

        self.runtime.print(msg, status=status, color=color, bold=bold)

    def _exec_command(self, cmd, _args):
        args = []
        for arg in _args:
            if (not ")" in arg) or (not "$(" in arg):
                args.append(arg)
                continue
            escaped = False
            checkvar = False
            invar = False
            args = []
            s = ""
            var = ""
            for c in arg:
                if not escaped:
                    if checkvar:
                        checkvar = False
                        if not c == '(':
                            s += '$' + c
                            continue
                        checkvar = False
                        invar = True
                        continue
                    elif invar:
                        if c == ')':
                            invar = False
                            val = ""
                            if not var in self.runtime.vars:
                                step(f"No such variable found, using empty : {var}", status="Warning", color="yellow", bold=True)
                            else:
                                val = str(self.runtime.vars[var])
                            s += val
                            continue
                        var += c
                        continue

                    if c == '\\':
                        escaped = True
                        continue
                    elif c == '$':
                        checkvar = True
                        continue
                else:
                    s += '\\'
                    escaped = False
                s += c
            args.append(s)

        if cmd == "print":
            self._handle_print(args)
        elif cmd == "exit":
            code = args[0] if args else 0
            self.runtime.exit(code)
        elif cmd == "system" and len(args) > 0:
            self.runtime.system(args)
        elif cmd == "exists" and len(args) > 0:
            self.runtime.exists(args)
        elif cmd == "read" and len(args) > 0:
            self.runtime.read(args[0])
        elif cmd == "write" and len(args) > 1:
            self.runtime.write(args[0], "\n".join(args[1:]))

        if cmd.startswith("$(") and cmd.endswith(")"): # Var
            cmd = cmd[2:]
            cmd = cmd[:-1]
            if cmd not in self.runtime.funcs:
                step(f"No such Variable/Function: {cmd}", status="Warning", color="yellow", bold=True)
                return None
            func = self.runtime.funcs[cmd]
            params = func.get("parameters", [])
            code = func.get("code", "")
            self.runtime.vars["ret"] = ""
            if not code:
                step(f"Call to empty function, skipping : {cmd}", status="Warning", color="yellow", bold=True)
                return None

            arg_len = len(args)
            param_len = len(params)
            
            if arg_len < param_len:
                step(f"Less arguments passed, skipping : {cmd}", status="Warning", color="yellow", bold=True)
                return None
            elif arg_len > param_len:
                step(f"Extra arguments passed, skipping extra : {cmd}", status="Warning", color="yellow", bold=True)
            
            for i, param in enumerate(params):
                if param in self.runtime.vars:
                    step(f"Parameter should not be already defined as a variable, this is a hazard. Skipping : {param}", status="Warning", color="yellow", bold=True)
                    return None
                elif param in ("ret"):
                    step(f"Parameter should not be reserved variables, this is a hazard. Skipping : {param}", status="Warning", color="yellow", bold=True)
                    return None
                self.runtime.vars[param] = args[i]
            
            self._exec_block(code)

            for i, param in enumerate(params):
                if param not in self.runtime.vars: continue
                self.runtime.vars.pop(param)

    def _exec_block(self, block:str):
        self.run(block)

    def run(self, data: str):
        try:
            for raw in data.splitlines():
                line = raw.split("$/")[0].strip()
                if not line:
                    continue

                if self.in_comment_block and not line.startswith("$*"):
                    continue

                if self.in_block and not line.startswith("$<"):
                    self.block += line + '\n'
                    continue

                # function+code enable
                if line.startswith("$!"):
                    self.funcs_allowed = True
                    continue

                # variable / metadata
                if line.startswith("$@"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    self.runtime.vars["SIGN"] = line[3:].strip()
                    continue

                # command
                if line.startswith("$#") and self.funcs_allowed:
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    cmdline = line[3:].strip()
                    cmd, args = self._parse_cmd_args(cmdline)
                    self._exec_command(cmd, args)
                    continue

                # function
                if line.startswith("$%") and self.funcs_allowed:
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    parts = shlex.split(line[3:])

                    self.runtime.funcs[parts[0]] = {
                        "name": parts[0],
                        "parameters": parts[1:] if len(parts) >= 2 else [],
                        "code": ""
                    }
                    self.cur_func = parts[0]
                    continue

                # repeat block
                if line.startswith("$^"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    rblock = line[3:]
                    if not rblock.isdigit():
                        step("Repeat Control needs a number, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    self.repeat_block = int(rblock)
                    continue

                # redirect output
                if line.startswith("$&"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    self.runtime.output = line[3:]
                    continue

                # comment block toggle
                if line.startswith("$*"):
                    self.in_comment_block = not self.in_comment_block
                    continue

                # code block open
                if line.startswith("$>"):
                    self.in_block = True
                    continue
                # code block close
                if line.startswith("$<"):
                    block = self.block
                    self.block = ""
                    if not self.in_block: continue
                    self.in_block = False
                    if self.cur_func != "":
                        if self.repeat_block > 0: self.repeat_block = 0
                        if self.cur_func not in self.runtime.funcs:
                            self.cur_func = ""
                            continue
                        self.runtime.funcs[self.cur_func]["code"] = block
                        self.cur_func = ""
                        continue

                    if self.repeat_block > 0:
                        for i in range(self.repeat_block):
                            self._exec_block(block)
                        self.repeat_block = 0
                        continue

                    if self.condition_active:
                        self.condition_active = False
                        if self.condition: self._exec_block(block)
                        continue
                    self._exec_block(block)
                    continue

                # set var
                if line.startswith("$="):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    varline = line[3:].strip()
                    var, args = self._parse_cmd_args(varline)
                    self.runtime.vars[var] = str(args[0]) if len(args) > 0 else ""
                    continue

                # unset var
                if line.startswith("$_!"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    var = line[3:].strip()
                    if not var in self.runtime.vars: continue
                    self.runtime.vars.pop(var)
                    continue

                # add var
                if line.startswith("$+"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    varline = line[3:].strip()
                    var, args = self._parse_cmd_args(varline)
                    val = str(args[0]) if len(args) > 0 else ""
                    ov = str(var) if not var in self.runtime.vars else str(self.runtime.vars[var])
                    if ov.isdigit() and val.isdigit(): self.runtime.vars[var] = int(ov) + int(val)
                    else: self.runtime.vars[var] = str(ov) + str(val)
                    continue
                # sub var
                if line.startswith("$-"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    varline = line[3:].strip()
                    var, args = self._parse_cmd_args(varline)
                    val = str(args[0]) if len(args) > 0 else ""
                    ov = str(var) if not var in self.runtime.vars else str(self.runtime.vars[var])
                    if ov.isdigit() and val.isdigit(): self.runtime.vars[var] = int(ov) - int(val)
                    else:
                        step("Cannot Subtract strings, Skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, status="Warning", color="yellow", bold=True)
                    continue
                # mul var
                if line.startswith("$_*"): # _ means extra suffix
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    varline = line[3:].strip()
                    var, args = self._parse_cmd_args(varline)
                    val = str(args[0]) if len(args) > 0 else ""
                    ov = str(var) if not var in self.runtime.vars else str(self.runtime.vars[var])
                    if ov.isdigit() and val.isdigit(): self.runtime.vars[var] = int(ov) * int(val)
                    elif ov.isdigit() and not val.isdigit(): self.runtime.vars[var] = int(ov) * str(val)
                    elif not ov.isdigit() and val.isdigit(): self.runtime.vars[var] = str(ov) * int(val)
                    else:
                        step("Cannot Multiply two strings, Skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, status="Warning", color="yellow", bold=True)
                    continue
                # div var
                if line.startswith("$_/"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    varline = line[3:].strip()
                    var, args = self._parse_cmd_args(varline)
                    val = str(args[0]) if len(args) > 0 else ""
                    ov = str(var) if not var in self.runtime.vars else str(self.runtime.vars[var])
                    if ov.isdigit() and val.isdigit(): self.runtime.vars[var] = int(ov) / int(val)
                    else:
                        step("Cannot Divide strings, Skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, status="Warning", color="yellow", bold=True)
                    continue

                # if var
                if line.startswith("$?"):
                    if len(line) < 3:
                        step("Invalid syntax, skipping", status="Warning", color="yellow", bold=True)
                        step_desc(line, color="yellow", bold=True)
                        continue
                    
                    self.condition = self._parse_condition(line[3:])
                    self.condition_active = True
                    continue
                # else var
                if line.startswith("$?!"):
                    self.condition = not self.condition
                    self.condition_active = True
                    continue
        except Exception:
            error("Something went wrong. Please check your file/syntax!")
            return None

class ProgressBar:
    def __init__(self, end_value:int=100, width:int=25, completed_char:str="#", remaining_char:str="-", prefix:str="", extended:bool=False, completed_color:str="", remaining_color:str="", other_color:str=""):
        self.end_val = end_value
        self.width = width
        self.cchar = completed_char
        self.rchar = remaining_char
        self.cur_val = 0
        self.prefix = prefix
        self.extended = extended
        self.ccolor = completed_color
        self.rcolor = remaining_color
        self.ocolor = other_color

    def draw(self):
        percentage = self.cur_val / self.end_val
        filled = int(percentage * self.width)

        percent_text = f"{percentage * 100:6.2f}%"
        if self.extended:
            printH(f"\r{f"    ...{self.prefix[-25:]}" if len(self.prefix) > 10 else self.prefix}[", FontEnabled=True, Font=TextFont(font_color=Color(self.ocolor)), endl="")
            printH(f"{self.cchar*filled}", FontEnabled=True, Font=TextFont(font_color=Color(self.ccolor)), endl="")
            printH(f"{self.rchar*(self.width - filled)}", FontEnabled=True, Font=TextFont(font_color=Color(self.rcolor)), endl="")
            printH(f"] {percent_text}", FontEnabled=True, Font=TextFont(font_color=Color(self.ocolor)), endl="")
        else:
            bar = (self.cchar * filled + self.rchar * (self.width - filled))
            sys.stdout.write(f"\r{self.prefix}[{bar}] {percent_text}")
            sys.stdout.flush()

    def set(self, value):
        self.cur_val = min(value, self.end_val)
        self.draw()

    def finish(self):
        self.cur_val = self.end_val
        self.draw()
        print()

class ConcurProgressBar:
    def __init__(self, end_value:int=100, width:int=25, completed_char:str="#", remaining_char:str="-", prefix:str="", extended:bool=False, completed_color:str="", remaining_color:str="", other_color:str=""):
        with concur_pb_lock:
            self.end_val = end_value
            self.width = width
            self.cchar = completed_char
            self.rchar = remaining_char
            self.cur_val = 0
            self.prefix = prefix
            self.extended = extended
            self.ccolor = completed_color
            self.rcolor = remaining_color
            self.ocolor = other_color
        self.draw() # ensure start draw

    def draw(self):
        with concur_pb_lock:
            cli.Cursor.SaveCursorPosition()

            percentage = self.cur_val / self.end_val
            filled = int(percentage * self.width)

            percent_text = f"{percentage * 100:6.2f}%"
            if self.extended:
                printH(f"{f"    ...{self.prefix[-25:]}" if len(self.prefix) > 10 else self.prefix}[", FontEnabled=True, Font=TextFont(font_color=Color(self.ocolor)), endl="")
                printH(f"{self.cchar*filled}", FontEnabled=True, Font=TextFont(font_color=Color(self.ccolor)), endl="")
                printH(f"{self.rchar*(self.width - filled)}", FontEnabled=True, Font=TextFont(font_color=Color(self.rcolor)), endl="")
                printH(f"] {percent_text}", FontEnabled=True, Font=TextFont(font_color=Color(self.ocolor)), endl="")
            else:
                bar = (self.cchar * filled + self.rchar * (self.width - filled))
                sys.stdout.write(f"{self.prefix}[{bar}] {percent_text}")
                sys.stdout.flush()

            cli.Cursor.RestoreCursorPosition()

    def set(self, value):
        self.cur_val = min(value, self.end_val)
        self.draw()

    def finish(self):
        self.cur_val = self.end_val
        self.draw()
        print()

def step(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"    -> {msg:<20} {status_str}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def step_desc(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"            {msg:<20} {status_str}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def step_nitem(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"{msg:<20} {status_str}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def jump(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"  :{status_str}: {msg:<20}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def eerror(msg, status="Critical Error", color="red", bold=True, code=0, type=step):
    type(msg=msg, status=status, color=color, bold=bold)
    os._exit(code)

def error(msg, status="Error", color="red", bold=True, type=step):
    type(msg=msg, status=status, color=color, bold=bold)

def new_item(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"{status_str} {msg:<20} ==>", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def sha256sum_file(path: str):
    h = hashlib.sha256()
    
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    
    return h.hexdigest()

def get_dir_size(path: str) -> int:
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += get_dir_size(entry.path)
                except OSError:
                    pass
    except OSError:
        pass
    return total

def download_file(url, path, pb_class=ProgressBar, autoHideShowCursor=True):
    if autoHideShowCursor:
        cli.Cursor.HideCursor()

    try:
        with urllib.request.urlopen(url) as response:
            total = int(response.getheader("Content-Length", 0))

            pb = pb_class(end_value=total, prefix=f"    {url} -> ", completed_color="green", remaining_color="grey", other_color="white", extended=True, width=25)

            downloaded = 0

            with open(path, "wb") as f:
                while True:
                    chunk = response.read(8192)

                    if not chunk:
                        break
                    f.write(chunk)

                    downloaded += len(chunk)
                    pb.set(downloaded)

            pb.finish()
    except URLError as e:
        error("Unable to Fetch! (Try checking your internet)")
        error(str(e), type=step_desc)
    except HTTPError as e:
        error("Unable to Fetch! (HTTP Error)")
        error(str(e), type=step_desc)
    except ContentTooShortError as e:
        error("Unable to Fetch! (Content was too short)")
        error(str(e), type=step_desc)
    except stimeout as e:
        error("Unable to Fetch! (Socket Timeout)")
        error(str(e), type=step_desc)
    except gaierror:
        error("Unable to Fetch! (Socket GAIError)")
        error(str(e), type=step_desc)

    if autoHideShowCursor:
        cli.Cursor.ShowCusor()

def atomic_fs_aquire_lock() -> int: # 0xEA = encoding active, 0xED = encoding disabled, 0xF0AADCCAEF = sign
    lock = f"""
$/ Autogenerated (Uses NFX Script Syntax)

$*
    Commands and control are done using '$' prefix with another symbol following it (control lines are to be started with these symbols)
    Prefixes -
    
    1. '$!' -> Function Start, Specifies the next lines contain executable NFX commands
    2. '$@' -> Sign, Specifies Identifier, App Name, and Version
    3. '$#' -> Command, Specifies a NFX command
    4. '$$' -> Literal, Just Specifies the literal '$'
    5. '$%' -> Function, Creates a Function
    6. '$^' -> Repeat, Allows to repeat a code-block
    7. '$&' -> Output Type, Specifies Output type ('step':DEFAULT, 'step_nitem', 'step_desc', 'jump', 'error', 'new_item')
    8. '$*' -> Multi-line Comment, Allows multi-line comments
    9. '$(' -> Variable Open, Specifies the next text within '$)' is a variable
    10. '$)' -> Variable Close, Specifies the closing of variable block
    11. '$/' -> Comment, Specifies single line comment
    12. '$>' -> Code Block Open, Specifies start of code block
    13. '$<' -> Code Block Close, Specifies end of code block

    Commands -
    1. 'print' -> Prints to Output
    2. 'exit' -> Exits
$*

$@ NFX/${APP_NAME}-v{VERSION}

PID={str(os.getpid())}

$!

$& new_item
$# print \"LockFile is LOCKED\"
$& step
$# print \"Locked by - NFX (PID-$(PID))\",color=red,bold=true
$# print \"Cannot Proceed Further - Exiting\",color=red,bold=true
$# exit ${NFX_ERROR_LOCKED}
-

""".encode("utf-8")
    
    sys = get_system_info()[0]
    if sys in POSIX_OSes:
        try:
            fd = os.open(LOCK_FILE_DEF, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, lock)
            return fd
        except FileExistsError:
            pass      
    elif sys == "windows":
        pass

def atomic_fs_release_lock(fd: int) -> None:
    os.close(fd)
    os.remove(LOCK_FILE_DEF)