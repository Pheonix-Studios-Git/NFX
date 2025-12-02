"""Downloading Manager File"""
import subprocess, os, shutil, json, stat, zipfile
import urllib.request

from phardwareitk.Extensions import *
from phardwareitk.Extensions.HyperOut import *
from __init__ import *
from config import *

from constants import BASE_DIR_DEF

EXEC = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

PPI_PAGE = "https://pheonix-studios-git.github.io/PPI/data/"

def fetch_repo(repo_url:str, download_dir:str, ppi:bool, package_json:dict) -> str:
    """
    Clone a git repo or copy local path to download_dir
    Returns path to cloned repo.
    """
    repo_name = os.path.basename(repo_url.rstrip("/")).replace(".zip", "")
    target_path = os.path.join(download_dir, repo_name)

    if ppi:
        repo_url = PPI_PAGE
        
    if os.path.exists(repo_url): # Local path
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(repo_url, target_path)
    else: # Assuming zip
        index = 0
        for obj in package_json:
            if obj.get("name", "") == repo_name:
                break
            index += 1
        else:
            printH("Error: No such package!", Font=TextFont(font_color=Color("red"), Bold=True), FontEnabled=True)
            os._exit(-6)
        os.mkdir(target_path)
        zippath = os.path.join(download_dir, repo_name + ".zip")
        try:
            urllib.request.urlretrieve(repo_url + package_json[index].get("zipfile", "Error404NotFound"), zippath)
            with zipfile.ZipFile(zippath, 'r') as zip_ref:
                zip_ref.extractall(target_path)
            os.remove(zippath)
        except zipfile.BadZipFile:
             printH("Not a Valid Zip File:", zippath, Font=TextFont(font_color=Color("red"), Bold=True), FontEnabled=True)
             os.remove(zippath)
             os.rmdir(target_path)
             os._exit(-4)
        except Exception:
            printH("Error Downloading the file:", repo_url + package_json[index].get("zipfile", "Error404NotFound"), "to", target_path, Font=TextFont(font_color=Color("red"), Bold=True), FontEnabled=True)
            os.rmdir(target_path)
            os._exit(-5)

    return target_path

def load_nfx_metadata(repo_path: str) -> dict:
    """Loads nfx file if found in pkg"""
    nfx_file = os.path.join(repo_path, "nfx.json")
    if not os.path.exists(nfx_file):
        raise FileNotFoundError(f"nfx.json not found in {repo_path}")
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def load_nfx_metadata_ex(nfx_file:str) -> dict:
    """Loads NFX MetaData (Extended)"""
    if not os.path.exists(nfx_file):
        raise FileNotFoundError(f"NFX Metadata file not found -> {nfx_file}")
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def copy_to_cache(repo_path: str, cache_dir: str, package_name: str) -> str:
    """Copy nfx to cache"""
    target = os.path.join(cache_dir, package_name)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(repo_path, target)
    shutil.rmtree(repo_path)
    return target

def finish_cache(package_name: str, metadata: dict):
    """Finish Working on the cache directory and generate necessary files"""
    return None # Does nothing for now
    
def install_binaries(metadata: dict, install_dir: str):
    """Installs Binaries for the pkg"""
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    downloaded_binaries = 0
    
    for bin_info in binaries:
        bin_os = [o.lower() for o in bin_info.get("Os", [])]
        bin_arch = [a.lower() for a in bin_info.get("Arch", [])]
        
        if os_name in bin_os and arch in bin_arch:
            src_path = os.path.join(metadata.get("CachePath", ""), bin_info["Path"])
            dest_path = os.path.join(install_dir, bin_info["Name"])
            
            if os.path.exists(dest_path):
                os.remove(dest_path)
            
            os.symlink(src_path, dest_path)
            os.chmod(dest_path, os.stat(dest_path).st_mode | EXEC)
            
            if bin_info.get("PostInstall"):
                run_post_install(os.path.join(metadata.get("CachePath", ""), bin_info["PostInstall"]))

            downloaded_binaries += 1

    if downloaded_binaries == 0:
        printH(f"Warning: The specified package doesn't support the machine! Continuing (Won't Install Binaries)", FontEnabled=True, Font=TextFont(font_color=Color("yellow")))

def remove_binaries(metadata: dict, install_dir: str):
    """Removes Binaries for the package"""
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    deleted_binaries = 0
    
    for bin_info in binaries:
        bin_os = [o.lower() for o in bin_info.get("Os", [])]
        bin_arch = [a.lower() for a in bin_info.get("Arch", [])]
        
        if os_name in bin_os and arch in bin_arch:
            src_path = os.path.join(metadata.get("CachePath", ""), bin_info["Path"])
            dest_path = os.path.join(install_dir, bin_info["Name"]) 
            
            os.unlink(dest_path)
            
            deleted_binaries += 1

    if deleted_binaries == 0:
        printH(f"Warning: The specified package doesn't support the machine! Continuing (No Binaries were installed in the first place, probably!)", FontEnabled=True, Font=TextFont(font_color=Color("yellow")))

def run_post_install(script_path: str):
    """Runs post install scripts"""
    os.chmod(script_path, os.stat(script_path).st_mode | EXEC)
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        subprocess.run([script_path], check=True)
    else:
        printH("PostInstall Failed to run!", FontEnabled=True, Font=TextFont(font_color=Color("red")))

def update_packages(args: list, config: Config):
    """Updates the package json file"""
    packages = os.path.join(BASE_DIR_DEF, "packages.json")
    
    try:
        urllib.request.urlretrieve(PPI_PAGE + "packages.json", packages)
    except Exception as e:
        printH("Error Downloading Packages List!", Font=TextFont(font_color=Color("red"), Bold=True), FontEnabled=True)
        os._exit(-5)

    printH("Synced Package List!", Font=TextFont(font_color=Color("cyan")), FontEnabled=True)

def search_packages(args: list, config: Config):
    """Searches for a package but via multiple queries"""
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    if not os.path.exists(packages_json):
        update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read())["packages"]

    for package in packages_data:
        name = package.get("name", "")
        for arg in args:
            if arg.lower() in name.lower():
                printH(
                    f"{name}:\n\t{package.get("description", "No Description")}",
                    FontEnabled=True,
                    Font = TextFont(
                        font_color = Color("cyan"),
                        Bold = True
                    )
                )

def search_package(query: str, args: list, config: Config):
    """Searches for a package but via single queries (Special Arguments Allowed)"""
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    if not os.path.exists(packages_json):
        update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read())["packages"]

    if "all" in args:
        for package in packages_data:
            name = package.get("name", "")
            printH(
                f"{name if name else "<No Name>"}:\n\t{package.get("description", "<No Description>")}",
                FontEnabled=True,
                Font = TextFont(
                    font_color = Color("cyan"),
                    Bold = True
                )
            )
        return None

    case = False
    if "case" in args:
        case = True
    else:
        query = query.lower()

    for package in packages_data:
        name = package.get("name", "")
        n = name
        if not case:
            n = name.lower()
        
        if query in n:
            printH(
                f"{name if name else "<No Name>"}:\n\t{package.get("description", "<No Description>")}",
                FontEnabled=True,
                Font = TextFont(
                    font_color = Color("cyan"),
                    Bold = True
                )
            )


def install_package(args: list, config: Config, repo_url: str = None, ppi: bool = True):
    """Installs a package"""
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")

    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    if not os.path.exists(install_dir):
        os.mkdir(install_dir)
    if not os.path.exists(packages_json):
        update_packages([], config)

    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read())["packages"]

    # fetch repo
    printH("Fetching repo...", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
    repo_path = fetch_repo(repo_url, download_dir, ppi, package_data)
    
    # load nfx.json
    printH("Loading package metadata...", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
    metadata = load_nfx_metadata(repo_path)
    metadata["CachePath"] = copy_to_cache(repo_path, cache_dir, metadata["Name"])
    
    # run post install scripts from main package
    if metadata.get("PostInstall"):
        printH(f"Running post-install script: {metadata['PostInstall']}", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
        run_post_install(os.path.join(metadata["CachePath"], metadata["PostInstall"]))
    
    # install binaries
    install_binaries(metadata, install_dir)

    finish_cache(metadata["Name"], metadata)
    
    printH(f"Package '{repo_url}' installed successfully!", FontEnabled=True, Font=TextFont(font_color=Color("green")))

def remove_package(args: list, config: Config, name: str):
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    if not os.path.exists(os.path.join(cache_dir, name)):
        printH(f"Package '{name}' was not found in cache, please don't alter the cache directory!", FontEnabled=True, Font=TextFont(font_color=Color("red")))
        os._exit(-7)

    metadata = load_nfx_metadata(os.path.join(cache_dir, name))
    
    remove_binaries(metadata, install_dir)
    shutil.rmtree(os.path.join(cache_dir, name))

    printH(f"Package '{name}' removed successfully!", FontEnabled=True, Font=TextFont(font_color=Color("green")))


def info_package(args: list, config: Config, name: str) -> tuple[dict, str]:
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    if not os.path.exists(os.path.join(cache_dir, name)):
        printH(f"Package '{name}' was not found in cache, please don't alter the cache directory!", FontEnabled=True, Font=TextFont(font_color=Color("red")))
        os._exit(-7)

    metadata = load_nfx_metadata(os.path.join(cache_dir, name))
    return metadata, os.path.join(cache_dir, name)
