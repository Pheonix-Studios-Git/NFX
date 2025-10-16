"""Main file"""

import os

from phardwareitk.Extensions import *
from phardwareitk.Extensions import HyperOut as Hout
from phardwareitk.Extensions import HyperIn as Hin
from phardwareitk.FileSystem import FileSystem as fs
from phardwareitk.CLI.cliToolKit import *

from constants import *
from config import *
from downloader import *

def print_help() -> None:
    """Prints help!"""
    Hout.printH(
        "NFX (Nova Pheonix Package Manager)",
        f"\tVersion: {VERSION}",
        f"\tDeveloper: {DEVELOPER}", 
        seperator="\n", 
        Flush=True, 
        FontEnabled=True, 
        Font=TextFont(
            font_color=Color("cyan"),
            Bold=True
        )
    )

    Hout.printH(
        "\nUsage: nfx <Option><Seperator><Args>",
        f"Seperators: {SEPERATORS}",
        "Quotes allowed for multi word arguments\n",
        seperator="\n",
        FontEnabled=True, 
        Flush=True, 
        Font=TextFont(
            font_color=Color("yellow"),
            Italic=True
        )
    )
    
    commands = [
        ("install:<pkg>", "Install one or more packages"),
        ("remove:<pkg>", "Remove packages"),
        ("search:<query>", "Search for a package"),
        ("update", "Update repository index"),
        ("upgrade", "Upgrade all packages"),
        ("config", "Show configuration"),
        ("genconfig", "Generate default config")
    ]

    for cmd, desc in commands:
        Hout.printH(
            f"{cmd}",
            f"\t{desc}",
            seperator="\n",
            FontEnabled=True,
            Flush=True,
            Font=TextFont(
                font_color=Color("cyan")
            )
        )

def generate_config(overwrite: bool = False):
    """Generate default config.json for NFX"""
    config_path = CONFIG_PATH_DEF
    if os.path.exists(config_path) and not overwrite:
        HyperOut.printH(f"Config already exists at {config_path}. Use overwrite arg to regenerate.", FontEnabled=True, Flush=True, Font=TextFont(
            font_color=Color("red"),
            Bold=True
        ))
        return

    default_config = Config()
    default_config.save(config_path)

    Hout.printH(
        "Default configuration generated successfully!",
        f"Path: {config_path}",
        seperator="\n",
        FontEnabled=True,
        Font=TextFont(font_color=Color("green"), Bold=True)
    )

def show_config() -> None:
    """Prints current configuration"""
    config = Config.load()
    Hout.printH(
        "NFX Configuration\n",
        FontEnabled=True,
        Flush=True,
        Font=TextFont(
            font_color=Color("cyan"),
            Bold=True,
        )
    )

    for key, value in config.__dict__.items():
        Hout.printH(
            f"{key}:",
            f"\t{value}",
            seperator="\n",
            FontEnabled=True,
            Flush=True,
            Font=TextFont(
                font_color=Color("cyan")
            )
        )

    Hout.printH("\nUse 'genconfig' to overwrite and generate the config", Flush=True, FontEnabled=True, Font=TextFont(
        font_color=Color("cyan"),
        Italic=True
    ))

def parse_arg(arg:str) -> tuple:
    """Parse arg using NFX format"""
    for sep in SEPERATORS:
        if sep in arg:
            key, val_str = arg.split(sep, 1)
            values = val_str.split(sep)
            return key, values

    return arg.strip(), []

def main(args:list[str]) -> None:
    """Main func"""
    parsed_args = []
    for arg in args:
        parsed_args.append(parse_arg(arg))

    config = Config.load()

    for key, values in parsed_args:
        if key == "help":
            print_help()
        elif key == "config":
            show_config()
        elif key == "genconfig":
            overwrite = False
            if len(values) > 0:
                overwrite = True if "overwrite" in values else False
            generate_config(overwrite=overwrite)
        elif key == "install":
            loc = values[0] if len(values) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            ppi = True
            if "local" in values:
                ppi = False
            install_package(values, config, loc)
        else:
            Hout.printH(f"Unknown Command - {key}:{", ".join(values)}", Flush=True, FontEnabled=True, Font=TextFont(
                font_color=Color("red"),
                Bold=True
            ))
            os._exit(-1)

if __name__ == "__main__":
    import sys
    sys.argv.pop(0)
    main(sys.argv)
