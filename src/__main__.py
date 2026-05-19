"""Main file"""

import os, sys
from datetime import datetime

from phardwareitk.Extensions import *
from phardwareitk.Extensions import HyperOut as Hout

from src.constants import *
from src.errors import *
from src.config import *
from src.downloader import *
from src.helpers import *
from src.pkgbuilder import *

def format_size(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024

def print_commands(cmds:list[tuple[Union[dict[str, list[tuple]], str], str]]) -> None:
    for cmd, desc in cmds:
        if isinstance(cmd, dict):
            for main_cmd, subcmds in cmd.items():
                print(
                    f"{main_cmd}",
                    f"    --> {desc}",
                    sep="\n"
                )
                if len(subcmds) > 0:
                    print("        Subcommands:")
                for subcmd, subdesc in subcmds:
                    print(
                        f"    ==> {subcmd}",
                        f"        --> {subdesc}",
                        sep="\n"
                    )
        else:
            print(
                f"{cmd}",
                f"    --> {desc}",
                sep="\n"
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
                ("local", "It is a local-repo/URL"),
                ("version=<version>", "Specify a specific version to install")
            ]
        }, "Install one or more packages (all dependencies are installed paralelly)"),
        ({
            "installs <packages>": [
                ("local", "They are a local-repo/URL"),
                ("version=<version>", "Specify a specific version of all packages to install")
            ]
        }, "Install one or more packages in parallel"),
        ({
            "upgrade <pkg>": [
                ("local", "It is a local-repo/URL"),
                ("all", "Upgrade all packages in sync (Downloaded packages)"),
                ("version=<version>", "Specify a specific version of the package to upgrade/downgrade to")
            ]
        }, "Updates one packages (all dependencies are installed paralelly)"),
        ({
            "upgrades <packages>": [
                ("local", "They are a local-repo/URL"),
                ("all", "Upgrade all packages in sync (Downloaded packages)"),
                ("version=<version>", "Specify a specific version of all packages to upgrade/downgrade to")
            ]
        }, "Updates one or more packages in sync (all dependencies are installed paralelly)"),
        ("remove <pkg>", "Removes a package"),
        ("removes <packages>", "Remove one or more packages in sync"),
        ({
            "info <pkg>": [
                ("license", "Show it's license"),
                ("author", "Show the author of the package"),
                ("doc", "Show the documentation of the package"),
                ("desc", "Show the description of the package"),
                ("modified", "Show the date the package was last modified")
            ]
        }, "Shows Information about installed packages"),
        ({
            "get-packages": [
                ("max-count=<number>", "Specify the maxiumum packages to display"),
                ("sort=<mode>", "Specify Sort mode, Modes: alpha (default), rev-alpha, time, rev-time, size, rev-size")
            ]
        }, "Shows all downloaded packages"),
        ("update", "Updates the package list"),
        ("cache-size", "Shows total cache size"),
        ("cache-clean", "Clears cache"),
        ({
            "searchs <queries>": [
                ("all", "Just show all, ignore the query"),
                ("case", "Make it Case-Sensitive"),
                ("show-versions=<count>", "Specifies to display <count> number or less versions."),
                ("show-all-versions", "Specifies to display all versions.")
            ]
        }, "Searches for packages which contain/are_equal to query/query_list (Not Case Sensitive by default)"),
        ({
            "search <query>": [
                ("all", "Just show all, ignore the query"),
                ("case", "Make it Case-Sensitive")
            ]
        }, "Search for packages which contain/are_equal to the query (Not Case Sensitive by default)"),
        ("status-code <code>", "Understand what the NFX status code means"),
        ("run-script <script path>", f"Run NFX Script version {VERSION}"),
        ("config", "Show configuration"),
        ({
            "genconfig": [
                ("overwrite", "Overwrite config, if already present?")
            ]
        }, "Generate default config"),
        ({
            "global_flags": [
                ("lockfile-info", "Incase the lockfile is locked, this flag forces NFXScript execution of the lockfile to get information on which PID is holding the lock and more")
            ]
        }, "Not a command, just flags that work on every command"),
        ("version", "Shows Current Version"),
        ("help", "Prints this help message")
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
    new_item("Generating config")
    jump("Checking config")

    config_path = CONFIG_PATH_DEF
    if os.path.exists(config_path) and not overwrite:
        step(f"Config already exists at {config_path}. Use overwrite arg to regenerate.", color="red", status="Error", bold=True)
        return

    new_item("Saving Config")
    default_config = Config()
    default_config.save(config_path)

    step("Default configuration generated successfully!", color="green", bold=True)
    step_desc(f"Path: {config_path}", color="green", bold=False)

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

    command: str = posix["command"]
    args_list: list = posix["args"]
    flags: set = posix["flags"]

    config = Config.load()

    if not command:
        print_usage()
        os._exit(1)

    lock = atomic_fs_aquire_lock(command, args_list, flags)
    if lock is None: return None

    if not os.path.exists(BASE_DIR_DEF):
        os.mkdir(BASE_DIR_DEF)

    if command == "help":
        print_help()
    elif command == "version":
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
    elif command == "config":
        show_config()
    elif command == "genconfig":
        overwrite = "overwrite" in flags
        generate_config(overwrite=overwrite)
    elif command == "install":
        pkg = args_list[0] if len(args_list) > 0 else eerror("No Package Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        install_package(pkg, flags, config)
    elif command == "installs":
        if len(args_list) <= 0:
            eerror("No Packages Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        install_packages(args_list, flags, config)
    elif command == "upgrade":
        pkg = None
        if "all" not in flags:
            pkg = args_list[0] if len(args_list) > 0 else eerror("No Package Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
            upgrade_package(pkg, flags, config)
        else:
            downloaded, _, __, ___, _____, ______ = get_all_packages(config)
            upgrade_packages(downloaded, flags, config)
    elif command == "upgrades":
        if len(args_list) <= 0 and "all" not in flags:
            eerror("No Packages Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        elif "all" in flags:
            downloaded, _, __, ___, _____, ______ = get_all_packages(config)
            upgrade_packages(downloaded, flags, config)
        else:
            upgrade_packages(args_list, flags, config)
    elif command == "remove":
        pkg = args_list[0] if len(args_list) > 0 else eerror("No Package Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        remove_package(flags, config, pkg)
    elif command == "removes":
        if len(args_list) <= 0:
            eerror("No Packages Specified!", code=NFX_ERROR_INVALID_ARGUMENT)
        remove_packages(args_list, flags, config)
    elif command == "info":
        loc = args_list[0] if len(args_list) > 0 else eerror("No Package Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        md, pkg_path = info_package(loc, flags, config)
        if len(flags) == 0:
            printH(f"Author: {md.get("Author", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
            printH(f"Description: {md.get("Description", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
            printH(f"Modified: {md.get("Build", {}).get("Date", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
        else:
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
            if "modified" in flags:
                printH(f"Modified: {md.get("Build", {}).get("Date", "Unknown")}\n", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
    elif command == "update":
        new_item("Updating Package List")
        jump("Syncing Package List")
        update_packages(flags, config)
    elif command == "searchs":
        queries = []
        if "all" not in flags:
            queries = args_list if len(args_list) > 0 else eerror("No Queries Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        search_packages(queries, flags, config)
    elif command == "search":
        query = ""
        if "all" not in flags:
            query = args_list[0] if len(args_list) > 0 else eerror("No Query Specified!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        search_package(query, flags, config)
    elif command == "get-packages":
        new_item("Getting Packages")
        
        max_count = -1
        for v in flags:
            if "max-count=" in v:
                c = v.replace("max-count=", "")
                if not str(c).isdigit():
                    eerror(f"'{c}' is not a number!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
                if not str(c) == "":
                    max_count = int(c)

        sort = "alpha"
        for v in flags:
            if "sort=" in v:
                sort = v.replace("sort=", "")
                if not sort in ["alpha", "rev-alpha", "time", "rev-time", "size", "rev-size"]:
                    eerror("sort must be either one of - alpha, rev-alpha, time, rev-time, size, rev-size", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        
        downloaded, dsize, dtime, _, __, ___ = get_all_packages(config, sort_mode=sort)

        jump("Installed Packages")
        if (len(downloaded) == 0):
            step("No Packages Exist", color="yellow", bold=True, status="Warning")
        else:
            for i, v in enumerate(downloaded):
                if i + 1 > max_count and max_count > 0: break
                step(f"{v} (Size: {format_size(dsize[i])}) at {datetime.fromtimestamp(dtime[i])}", color="green", bold=True)
    elif command == "cache-size":
        new_item("Getting Cache Size")
        if not os.path.exists(config.cache_dir):
            step("No Cache Exists!", color="green", bold=True)
        else:
            step("Cache Size: " + format_size(get_dir_size(config.cache_dir)), color="green", bold=True)
    elif command == "cache-clean":
        new_item("Clearing Cache")
        if not os.path.exists(config.cache_dir):
            step("No Cache Exists", color="green", bold=True)
        else:
            jump("Removing Cache Directory and cleaning cache")
            shutil.rmtree(config.cache_dir)
            step("Cleared Cache", color="green", bold=True)
    elif command == "build-pkg":
        # if len(args_list) < 1:
        #     eerror("Please specify a BUILD file!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        # pkg_build(args_list, flags, config)
        eerror("This command is under development, users are not allowed to use it!", code=NFX_ERROR_NOT_IMPLEMENTED)
    elif command == "status-code":
        if len(args_list) < 1:
            eerror("Please provide a status code", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        elif not args_list[0].isdigit():
            eerror("Please provide an integer status code!", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)

        code = int(args_list[0])
        new_item(f"Status Code: {code}")
        step_desc(NFX_ERROR_MESSAGES.get(code, "Unknown Status Code"), status="Meaning", color="red", bold=False)
    elif command == "run-script":
        if len(args_list) < 1:
            eerror("Please provide path to script", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)
        file = args_list[0]
        if not os.path.exists(file):
            eerror(f"Provided file '{file}' doesn't exist!", code=NFX_ERROR_FILE_NOT_FOUND)
        d = ""
        with open(file, "r") as f:
            f.seek(0)
            d = f.read()
        vars = {}
        funcs = {}
        inbuilt_funcs = {
            "step": step,
            "step_desc": step_desc,
            "step_nitem": step_nitem,
            "new_item": new_item,
            "jump": jump,
            "error": error
        }
        rte = NFXRuntime(output="step", inbuilt_funcs=inbuilt_funcs, vars=vars, funcs=funcs)
        vm = NFXScriptVM(rte)
        vm.run(d)
    else:
        eerror(f"Unknown Command - {command}", type=step_nitem, code=NFX_ERROR_INVALID_ARGUMENT)

    atomic_fs_release_lock(lock)

if __name__ == "__main__":
    import sys
    sys.argv.pop(0)
    main(sys.argv)
