"""Main file"""

import os, sys, site

import shlex

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
        "\nUsage: nfx <Option> <Args> [--<Flags>]\n",
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
            "install <pkg>": [
                ("local", "It is a local-repo/URL")
            ]
        }, "Install one or more packages (all dependencies are installed paralelly)"),
        ("installs <packages>", "Install one or more packages in parallel"),
        ("remove <pkg>", "Removes a package"),
        ("removes <packages>", "Remove one or more packages in parallel"),
        ({
            "info <pkg>": [
                ("license", "Show it's license"),
                ("author", "Show the author of the package"),
                ("doc", "Show the documentation of the package"),
                ("desc", "Show the description of the package")
            ]
        }, "Shows Information about the package"),
        ("update", "Updates the package list"),
        ("clean", "Clears cache"),
        ({
            "searchs <queries>": [
                ("all", "Just show all, ignore the query"),
                ("case", "Make it Case-Sensitive")
            ]
        }, "Searches for packages which contain/are_equal to query/query_list (Not Case Sensitive by default)"),
        ({
            "search <query>": [
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
        "\nUsage: nfx <Option> <Args> [--<Flags>]\n",
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

def parse_posix_args(argv: list[str]) -> dict:
    """
    POSIX-style argument parser
    Supports:
        nfx install pac --local
        nfx info pac --author --desc
    """

    result = {
        "command": None,
        "args": [],
        "flags": set()
    }

    if not argv:
        return result

    result["command"] = argv[0]
    rest = argv[1:]

    i = 0
    while i < len(rest):
        arg = rest[i]

        # flags
        if arg.startswith("--"):
            result["flags"].add(arg[2:])
        elif arg.startswith("-") and len(arg) > 1:
            result["flags"].add(arg[1:])
        else:
            result["args"].append(arg)

        i += 1

    return result

def main(args:list[str]) -> None:
    """Main func"""
    if sys.platform.startswith("win"):
        enable_winterminal()
    
    posix = parse_posix_args(args)

    command = posix["command"]
    args_list = posix["args"]
    flags = posix["flags"]

    config = Config.load()

    if not command:
        print_usage()
        os._exit(1)

    if not os.path.exists(BASE_DIR_DEF):
        os.mkdir(BASE_DIR_DEF)

    if command == "help":
        print_help()
    elif command == "config":
        show_config()
    elif command == "genconfig":
        overwrite = "overwrite" in flags
        generate_config(overwrite=overwrite)
    elif command == "install":
        pkg = args_list[0] if len(args_list) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        install_package(pkg, args_list, config)
    elif command == "installs":
        if len(args_list) <= 0:
            Hout.exitH(-41, "No Packages Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        install_packages(args_list, flags, config)
    elif command == "remove":
        pkg = args_list[0] if len(args_list) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        remove_package(flags, config, pkg)
    elif command == "removes":
        if len(args_list) <= 0:
            Hout.exitH(-41, "No Packages Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        remove_packages(args_list, flags, config)
    elif command == "info":
        loc = args_list[0] if len(args_list) > 0 else Hout.exitH(-41, "No Package Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        md, pkg_path = info_package(loc, flags, config)
        if len(flags) == 1:
            args_list.append("author")
            args_list.append("desc")

        if "author" in flags:
            printH(f"Author: {md.get("Author", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
        if "desc" in flags:
            printH(f"Description: {md.get("Description", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
        if "license" in flags:
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
        if "doc" in flags:
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
    elif command == "update":
        update_packages(flags, config)
    elif command == "searchs":
        queries = args_list if len(args_list) > 0 else Hout.exitH(-41, "No Queries Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        search_packages(queries, flags, config)
    elif command == "search":
        query = args_list[0] if len(args_list) > 0 else Hout.exitH(-41, "No Query Specified!", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
        args_list.pop(0)
        search_package(query, flags, config)
    elif command == "clean":
        shutil.rmtree(config.cache_dir)
        printH("Cleared Cache", FontEnabled=True, Font=TextFont(font_color=Color("green"),Bold=True))
    else:
        Hout.printH(f"Unknown Command - {command} {" ".join(args_list)}", Flush=True, FontEnabled=True, Font=TextFont(
            font_color=Color("red"),
            Bold=True
        ))
        os._exit(-1)

if __name__ == "__main__":
    import sys
    sys.argv.pop(0)
    main(sys.argv)
