"""Main file"""

import os, sys

from phardwareitk.Extensions import *
from phardwareitk.Extensions import HyperOut as Hout
from phardwareitk.Extensions import HyperIn as Hin
from phardwareitk.FileSystem import FileSystem as fs
from phardwareitk.CLI.cliToolKit import *

from constants import *
from config import *
from downloader import *

def print_commands(cmds:list[tuple[Union[dict[str, list[tuple]], str], str]]) -> None:
    for cmd, desc in cmds:
        if isinstance(cmd, dict):
            for main_cmd, subcmds in cmd.items():
                Hout.printH(
                    f"{main_cmd}",
                    f"\t{desc}",
                    seperator="\n",
                    FontEnabled=True,
                    Flush=True,
                    Font=TextFont(
                        font_color=Color("cyan")
                    )
                )
                for subcmd, subdesc in subcmds:
                    Hout.printH(
                        f"\t{subcmd}",
                        f"\t\t{subdesc}",
                        seperator="\n",
                        FontEnabled=True,
                        Flush=True,
                        Font=TextFont(
                            font_color=Color("cyan"),
                            Italic=True
                        )
                    )
        else:
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
        ({
            "install:<pkg>": [
                ("local", "It is a local-repo/URL")
            ]
        }, "Install one or more packages"),
        ("installs:<packages>", "Install one or more packages in parallel (Faster)"),
        ("remove:<pkg>", "Remove packages"),
        ("removes:<packages>", "Remove one or more packages in parallel (Faster)"),
        ({
            "info:<pkg>": [
                ("license", "Show it's license"),
                ("author", "Show the author of the package"),
                ("doc", "Show the documentation of the package"),
                ("desc", "Show the description of the package")
            ]
        }, "Shows Information about the package"),
        ("update", "Updates the package list"),
        ("searchs:<queries>", "Searches for packages which contain/are_equal to the query/query_list (Not Case Sensitive)"),
        ({
            "search:<query>": [
                ("all", "Just show all, ignore the query"),
                ("case", "Make it Case-Sensitive")
            ]
        }, "Search for packages which contain/are_equal to the query (Not Case Sensitive by default)"),
        ("config", "Show configuration"),
        ({
            "genconfig": [
                ("overwrite", "Overwrite config, if already present?")
            ]
        }, "Generate default config")
    ]

    print_commands(commands)

def print_usage() -> None:
    """Prints the usage!"""
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
        "Use 'help' for more information!\n",
        seperator="\n",
        FontEnabled=True, 
        Flush=True, 
        Font=TextFont(
            font_color=Color("yellow"),
            Italic=True
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
    arg = arg.strip()
    
    # Split key and value at first separator
    key = arg
    val_str = ""
    for sep in SEPERATORS:
        if sep in arg:
            key, val_str = arg.split(sep, 1)
            key = key.strip()
            val_str = val_str.strip()
            break

    # Parse sub-values respecting quotes
    values: list = []
    sub_value = ""
    in_quotes = False

    i = 0
    while i < len(val_str):
        char = val_str[i]

        if char == '"':
            # Toggle in_quotes
            in_quotes = not in_quotes
            i += 1
            continue

        if char in SEPERATORS and not in_quotes:
            # End of sub-value
            values.append(sub_value.strip())
            sub_value = ""
        else:
            sub_value += char

        i += 1

    if sub_value:
        values.append(sub_value.strip())

    return key, values

def main(args:list[str]) -> None:
    """Main func"""
    if sys.platform.startswith("win"):
        enable_winterminal()
    
    parsed_args: list[tuple[str, list[str]]] = []
    for arg in args:
        parsed_args.append(parse_arg(arg))

    config = Config.load()

    if len(parsed_args) == 0:
        print_usage()
        os._exit(1)

    if not os.path.exists(BASE_DIR_DEF):
        os.mkdir(BASE_DIR_DEF)

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
            subpkg = ""
            if "local" in values:
                ppi = False
            if "subpkg" in values:
                idx = values.index("subpkg")
                if len(values) < idx + 1:
                    Hout.printH(
                        "Command 'subpkg' requires an argument!\n\nExample: 'install:somepackage:subpkg:\\\"Name of sub-package\\\"\n",
                        Font=TextFont(
                            font_color=Color("red"),
                            Bold=True
                        ),
                        FontEnabled=True
                    )
                    os._exit(-2)
            install_package(values, config, loc, ppi)
        elif key == "installs":
            if len(values) <= 0:
                Hout.exitH(-41, "No Packages Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            install_packages(values, [], config)
        elif key == "remove":
            loc = values[0] if len(values) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            remove_package(values, config, loc)
        elif key == "removes":
            if len(values) <= 0:
                Hout.exitH(-41, "No Packages Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            remove_packages(values, [], config)
        elif key == "info":
            loc = values[0] if len(values) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            md, pkg_path = info_package(values, config, loc)
            if len(values) == 1:
                values.append("author")
                values.append("desc")

            if "author" in values:
                printH(f"Author: {md.get("Author", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
            if "desc" in values:
                printH(f"Description: {md.get("Description", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
            if "license" in values:
                printH("License:\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
                if os.path.exists(os.path.join(pkg_path, md.get("License", "LICENSE"))):
                    data = ""
                    with open(os.path.join(pkg_path, md.get("License", "LICENSE")), "r") as f:
                        f.seek(0)
                        data = f.read()
                    print(data)
                    print("\n\n")
                else:
                    print("Not Found!\n\n")
            if "doc" in values:
                printH("Documentation:\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
                if os.path.exists(os.path.join(pkg_path, md.get("Readme", "README.md"))):
                    data = ""
                    with open(os.path.join(pkg_path, md.get("Readme", "README.md")), "r") as f:
                        f.seek(0)
                        data = f.read()
                    print(data)
                    print("\n\n")
                else:
                    print("Not Found!\n\n")
        elif key == "update":
            update_packages([], config)
        elif key == "searchs":
            queries = values if len(values) > 0 else Hout.exitH(-41, "No Queries Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            search_packages(queries, config)
        elif key == "search":
            query = values[0] if len(values) > 0 else Hout.exitH(-41, "No Query Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            values.pop(0)
            search_package(query, values, config)
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
