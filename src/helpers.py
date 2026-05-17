import os

from phardwareitk.Extensions import *
from phardwareitk.Extensions.HyperOut import *
from phardwareitk.CLI import cliToolKit as cli

import urllib
from urllib.error import URLError, HTTPError, ContentTooShortError
import hashlib
import threading
from socket import timeout as stimeout
from socket import gaierror

concur_pb_lock = threading.Lock()

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
