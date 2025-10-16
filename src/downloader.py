"""Downloading Manager File"""
import subprocess, os, shutil, json, stat
from phardwareitk.Extensions import *
from phardwareitk.Extensions.HyperOut import *
from __init__ import *
from config import *

EXEC = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

def fetch_repo(repo_url:str, download_dir:str) -> str:
    """
    Clone a git repo or copy local path to download_dir
    Returns path to cloned repo.
    """
    repo_name = os.path.basename(repo_url.rstrip("/")).replace(".git", "")
    target_path = os.path.join(download_dir, repo_name)
    
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    
    if os.path.exists(repo_url): # Local path
        shutil.copytree(repo_url, target_path)
    else: # Git URL
        subprocess.run(["git", "clone", repo_url, target_path], check=True)

    return target_path

def load_nfx_metadata(repo_path: str) -> dict:
    """Loads nfx file if found in pkg"""
    nfx_file = os.path.join(repo_path, "nfx.json")
    if not os.path.exists(nfx_file):
        raise FileNotFoundError(f"nfx.json not found in {repo_path}")
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def copy_to_cache(repo_path: str, cache_dir: str, package_name: str) -> str:
    """Copy nfx to cache"""
    target = os.path.join(cache_dir, package_name)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(repo_path, target)
    return target

def install_binaries(metadata: dict, install_dir: str):
    """Installs Binaries for the pkg"""
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    
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

def run_post_install(script_path: str):
    """Runs post install scripts"""
    os.chmod(script_path, os.stat(script_path).st_mode | EXEC)
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        subprocess.run([script_path], check=True)
    else:
        printH("PostInstall Failed to run!", FontEnabled=True, Font=TextFont(font_color=Color("red")))

def install_package(args: list, config: Config, repo_url: str = None):
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    # fetch repo
    printH("Fetching repo...", FontEnabled=True, Font=TextFont(font_color=Color("cyan")))
    repo_path = fetch_repo(repo_url or "PPI_DEFAULT_URL", download_dir)
    
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
    
    printH(f"Package {metadata['Name']} installed successfully!", FontEnabled=True, Font=TextFont(font_color=Color("green")))

