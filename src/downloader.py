"""Downloading Manager File"""
import subprocess, os, shutil, json, stat, zipfile, urllib.request
import concurrent.futures

from phardwareitk.CLI import cliToolKit as cli

from urllib.error import URLError, HTTPError, ContentTooShortError
from socket import timeout as stimeout
from socket import gaierror

from src import *
from src.config import *
from src.helpers import *
from src.constants import BASE_DIR_DEF, SYSTEM

from datetime import datetime

EXEC = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

PPI_PAGE = "https://pheonix-studios-git.github.io/PPI/data/"

CONTROL_DICT = {"updated packages": False}

def fetch_repo(repo_url:str, cache_dir:str, ppi:bool, package_json:dict, pb=ProgressBar) -> Optional[str]:
    """
    Clone a git repo or copy local path to cache_dir
    Returns path to cloned repo.
    """
    repo_name = os.path.basename(repo_url.rstrip("/")).replace(".zip", "")
    target_path = os.path.join(cache_dir, repo_name)
    force_cache = False
    rem_on_bad = True

    if os.path.exists(target_path):
        return target_path

    if ppi:
        repo_url = PPI_PAGE
        
    if os.path.exists(repo_url): # Local path
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        if os.path.isdir(repo_url):
            shutil.copytree(repo_url, target_path)
            return target_path
        elif os.path.isfile(repo_url):
            # Assume ZIP
            zippath = repo_url
            sigpath = ""
            force_cache = True
            rem_on_bad = False
    else: # Assuming zip
        index = 0
        for obj in package_json:
            if obj.get("name", "") == repo_name:
                break
            index += 1
        else:
            error("Could not fetch package as it was not found!")
            return None
        os.mkdir(target_path)
        zippath = os.path.join(cache_dir, repo_name + ".zip")
        sigpath = os.path.join(cache_dir, repo_name + ".sig")

    if os.path.exists(zippath):
        try:
            with zipfile.ZipFile(zippath, 'r') as zip_ref:
                if force_cache:
                    shutil.copy(zippath, os.path.join(cache_dir, repo_name + ".zip"))
                zip_ref.extractall(target_path) # Keep downloaded cache
        except zipfile.BadZipFile:
            if rem_on_bad: os.remove(zippath)
            if os.path.exists(target_path): os.rmdir(target_path)
            error(f"Package doesn't have a valid zip file")
            return None
        except Exception as e:
            if os.path.exists(target_path): os.rmdir(target_path)
            error(f"Error Downloading the ZIP '{zippath}' to '{target_path}'\n\t{e}")
            return None
    else:
            try:
                download_file(repo_url + package_json[index].get("zipfile", "Error404NotFound"), zippath, pb_class=pb)
                with zipfile.ZipFile(zippath, 'r') as zip_ref:
                    zip_ref.extractall(target_path) # Keep downloaded cache
            except zipfile.BadZipFile:
                if rem_on_bad: os.remove(zippath)
                if os.path.exists(target_path): os.rmdir(target_path)
                error(f"Package doesn't have a valid zip file")
                return None
            except Exception as e:
                if os.path.exists(target_path): os.rmdir(target_path)
                error(f"Error Downloading the ZIP '{repo_url + package_json[index].get("zipfile", "Error404NotFound")}' to '{target_path}'\n\t{e}")
                return None

            if package_json[index].get("signed_zipfile", "") != "":
                try:
                    download_file(repo_url + package_json[index].get("signed_zipfile", "Error404NotFound"), sigpath, pb_class=pb)
                except Exception as e:
                    if os.path.exists(target_path): os.rmdir(target_path)
                    error(f"Error Downloading the ZIP SIGNATURE '{repo_url + package_json[index].get("signed_zipfile", "Error404NotFound")}' to '{sigpath}'\n\t{e}")
                    return None

    return target_path

def load_nfx_metadata(repo_path: str) -> Optional[dict]:
    """Loads nfx file if found in pkg"""
    nfx_file = os.path.join(repo_path, "nfx.json")
    if not os.path.exists(nfx_file):
        error("Metadata file (nfx.json) not found!")
        return None
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def load_nfx_metadata_ex(nfx_file:str) -> dict:
    """Loads NFX MetaData (Extended)"""
    if not os.path.exists(nfx_file):
        error("Metadata file (nfx.json) not found!")
        return None
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def copy_to_downloads(repo_path: str, download_dir: str, package_name: str) -> str:
    """Copy nfx to downloads"""
    target = os.path.join(download_dir, package_name)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(repo_path, target)
    shutil.rmtree(repo_path)
    return target

def finish_download(package_name: str, metadata: dict):
    """Finish Working on the download directory and generate necessary files"""
    return None # Does nothing for now
    
def install_binaries(metadata: dict, install_dir: str) -> bool:
    """Installs Binaries for the pkg"""
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    downloaded_binaries = 0
    
    for bin_info in binaries:
        bin_os = [o.lower() for o in bin_info.get("Os", [])]
        bin_arch = [a.lower() for a in bin_info.get("Arch", [])]
        
        if os_name in bin_os and arch in bin_arch:
            src_path = os.path.join(metadata.get("DownloadPath", ""), bin_info.get("Path", ""))
            dest_path = os.path.join(install_dir, bin_info.get("Name", ""))
            
            if SYSTEM == "Windows" and not os.path.exists(src_path):
                root, ext = os.path.splitext(src_path)
                if ext.lower() != ".exe":
                    alt_path = src_path + ".exe"
                    if os.path.exists(alt_path):
                        src_path = alt_path
                root, ext = os.path.splitext(dest_path)
                if ext.lower() != ".exe":
                    alt_path = dest_path + ".exe"
                    if os.path.exists(alt_path):
                        dest_path = alt_path
            src_path = os.path.normcase(src_path)
            dest_path = os.path.normcase(dest_path)

            if os.path.exists(dest_path):
                os.remove(dest_path)
            
            try:
                os.symlink(src_path, dest_path)
                os.chmod(dest_path, os.stat(dest_path).st_mode | EXEC)
            except PermissionError:
                error("Insufficient Permissions!")
                return False
            
            if bin_info.get("PostInstall"):
                run_post_install(os.path.join(metadata.get("DownloadPath", ""), bin_info.get("PostInstall", "")))

            downloaded_binaries += 1

    if downloaded_binaries == 0:
        step("The specified package doesn't support the machine! Continuing (Won't Install Binaries)", status="Warning", color="yellow", bold=True)

    return True

def remove_binaries(metadata: dict, install_dir: str) -> bool:
    """Removes Binaries for the package"""
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    deleted_binaries = 0
    
    for bin_info in binaries:
        bin_os = [o.lower() for o in bin_info.get("Os", [])]
        bin_arch = [a.lower() for a in bin_info.get("Arch", [])]
        
        if os_name in bin_os and arch in bin_arch:
            src_path = os.path.join(metadata.get("DownloadPath", ""), bin_info.get("Path", ""))
            dest_path = os.path.join(install_dir, bin_info.get("Name", "")) 
            
            if SYSTEM == "Windows" and not os.path.exists(src_path):
                root, ext = os.path.splitext(src_path)
                if ext.lower() != ".exe":
                    alt_path = src_path + ".exe"
                    if os.path.exists(alt_path):
                        src_path = alt_path
                root, ext = os.path.splitext(dest_path)
                if ext.lower() != ".exe":
                    alt_path = dest_path + ".exe"
                    if os.path.exists(alt_path):
                        dest_path = alt_path
            src_path = os.path.normcase(src_path)
            dest_path = os.path.normcase(dest_path)

            try:
                if (os.path.exists(dest_path)): os.unlink(dest_path)
            except PermissionError:
                error("Insufficient Permissions")
                return False
            
            deleted_binaries += 1

    if deleted_binaries == 0:
        step("The specified package doesn't support the machine! Continuing (No Binaries were installed in the first place, probably!)", status="Warning", color="yellow", bold=True)

    return True

def run_post_install(script_path: str) -> bool:
    """Runs post install scripts"""
    os.chmod(script_path, os.stat(script_path).st_mode | EXEC)
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        subprocess.run([script_path], check=True)
        return True
    else:
        error("Post install failed to run (Most likely a permission or path issue)")
        return False

def verify_package(repo_path: str, cache_dir: str, metadata: dict, config: Config):
    "Verifies the package and takes in user input as well, uses ED22519 and SHA256"
    # Verify Zip signature
    repo_name = os.path.basename(repo_path)
    sigpath = os.path.join(cache_dir, repo_name + ".sig")
    zippath = os.path.join(cache_dir, repo_name + ".zip")
    if not os.path.exists(zippath):
        error("Package has lost its cached zipfile")
        return False
    if (os.path.exists(sigpath)):
        try:
            result = subprocess.run(
                [
                    "ssh-keygen",
                    "-Y", "verify",
                    "-f", os.path.join(metadata["DownloadPath"], metadata.get("Build", {}).get("AllowedSigners", "")),
                    "-I", metadata.get("Build", {}).get("SignatureIdentity", ""),
                    "-n", "file",
                    "-s", sigpath,
                ],
                input=open(zippath, "rb").read(),
                capture_output=True,
            )
            if result.returncode != 0:
                if config.security_level in ("max", "very-high", "high", "medium", "low"):
                    error("Package ED25519 Signature Match Failed")
                    return False
                step("Package is tampered with (Risk: Very High), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
                if input("").lower() not in ("y", "yes", "yeah", "yea"):
                    return False
        except Exception as e:
            if config.security_level in ("max", "very-high", "high", "medium", "low"):
                error("'ssh-keygen' was not found, hence 'ZIP' verification can't be done!")
                return False
            step("'ssh-keygen' was not found, hence 'ZIP' verification is skipped (Risk: Medium), continue (y/N): ", status="Input", color="yellow", bold=True)
            if input("").lower() not in ("y", "yes", "yeah", "yea"):
                return False
    else:
        if config.security_level in ("max", "very-high", "high", "medium"):
            error("Package ED25519 Signature Match Failed")
            return False
        step("Package is unverified (Risk: High), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
        if input("").lower() not in ("y", "yes", "yeah", "yea"):
            return False

    # Verify Binary hashes (only the supported one)
    os_name, arch = get_system_info()
    binaries = metadata.get("Binaries", [])
    
    for bin_info in binaries:
        bin_os = [o.lower() for o in bin_info.get("Os", [])]
        bin_arch = [a.lower() for a in bin_info.get("Arch", [])]
        
        if os_name in bin_os and arch in bin_arch:
            src_path = os.path.join(metadata.get("DownloadPath", ""), bin_info.get("Path", ""))
            
            if SYSTEM == "Windows" and not os.path.exists(src_path):
                root, ext = os.path.splitext(src_path)
                if ext.lower() != ".exe":
                    alt_path = src_path + ".exe"
                    if os.path.exists(alt_path):
                        src_path = alt_path

            src_path = os.path.normcase(src_path)
            if not os.path.exists(src_path):
                error(f"Package lost its binaries! ({src_path})")
                return False
            hash_ = sha256sum_file(src_path)
            if hash_ != bin_info.get("Sha256", ""):
                if config.security_level in ("max", "very-high", "high"):
                    error("Package Binary SHA256 HASH Match Failed")
                    return False
                step("Package has invalid sha256 hashed binaries (Risk: Medium), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
                if input("").lower() not in ("y", "yes", "yeah", "yea"):
                    return False
    
    return True

def update_packages(args: list, config: Config):
    """Updates the package json file"""
    if CONTROL_DICT["updated packages"]:
        return None
    url = PPI_PAGE + "packages.json"
    packages = os.path.join(BASE_DIR_DEF, "packages.json")

    try:
        with urllib.request.urlopen(url) as response:
            remote_data = json.load(response)
    except URLError as e:
        error("Unable to Fetch! (Try checking your internet)")
        eerror(str(e), type=step_desc)
    except HTTPError as e:
        error("Unable to Fetch! (HTTP Error)")
        eerror(str(e), type=step_desc)
    except ContentTooShortError as e:
        error("Unable to Fetch! (Content was too short)")
        eerror(str(e), type=step_desc)
    except stimeout as e:
        error("Unable to Fetch! (Socket Timeout)")
        eerror(str(e), type=step_desc)
    except gaierror:
        error("Unable to Fetch! (Socket GAIError)")
        eerror(str(e), type=step_desc)

    needed = False
    if not os.path.exists(packages):
        needed = True
    else:
        with open(packages, "r") as f:
            local_data = json.load(f)

        needed = True if datetime.strptime(remote_data.get("modified", "1970-01-01 00:00"), "%Y-%m-%d %H:%M") > datetime.strptime(local_data.get("modified", "1970-01-01 00:00"), "%Y-%m-%d %H:%M") else False
    
    jump("Updating Package List")
    if (not needed):
        step("Package List up-to-date!", color="green", bold=True)
        CONTROL_DICT["updated packages"] = True
        return None

    try:
        urllib.request.urlretrieve(PPI_PAGE + "packages.json", packages)
    except Exception as e:
        if os.path.exists(packages):
            step("Error Downloading Packages List, skipping", status="Warning", color="yellow", bold=True)
            return False
        else:
            eerror("Error Downloading Packages List!")

    step("Synced Package List!", color="green", bold=True)
    CONTROL_DICT["updated packages"] = True

def get_all_packages(config: Config, sort_mode:str="alpha") -> tuple[list[str], list[int], list[float], list[str], list[int], list[float]]:
    """
    Provides all packages
    
    Returns ([Downloaded Packages], [Downloaded Packages Size], [Downloaded Packages Time], [Installed Packages], [Installed Packages Size], [Installed Packages Time])
    """
    download_dir = config.download_dir
    install_dir = config.install_dir

    downloaded = []
    if os.path.exists(download_dir):
        for item in os.listdir(download_dir):
            path = os.path.join(download_dir, item)
            if os.path.isdir(path):
                downloaded.append((
                    item,
                    get_dir_size(path),
                    os.path.getmtime(path)
                ))
    else:
        step("No download dir found!", status="Warning", color="yellow", bold=True)

    installed = []
    if os.path.exists(install_dir):
        for item in os.listdir(install_dir):
            path = os.path.join(install_dir, item)
            if os.path.islink(path):
                installed.append((
                    item,
                    os.path.getsize(path),
                    os.path.getmtime(path)
                ))
    else:
        step("No installation dir found!", status="Warning", color="yellow", bold=True)

    if sort_mode == "alpha":
        key_fn = lambda x: x[0].lower()
        reverse = False
    elif sort_mode == "rev-alpha":
        key_fn = lambda x: x[0].lower()
        reverse = True
    elif sort_mode == "time":
        key_fn = lambda x: x[2]
        reverse = False
    elif sort_mode == "size":
        key_fn = lambda x: x[1]
        reverse = False
    elif sort_mode == "rev-time":
        key_fn = lambda x: x[2]
        reverse = True
    elif sort_mode == "rev-size":
        key_fn = lambda x: x[1]
        reverse = True
    else:
        key_fn = None

    if key_fn:
        downloaded.sort(key=key_fn, reverse=reverse)
        installed.sort(key=key_fn, reverse=reverse)

    d_names  = [x[0] for x in downloaded]
    d_sizes  = [x[1] for x in downloaded]
    d_times  = [x[2] for x in downloaded]

    i_names  = [x[0] for x in installed]
    i_sizes  = [x[1] for x in installed]
    i_times  = [x[2] for x in installed]

    return d_names, d_sizes, d_times, i_names, i_sizes, i_times

def package_exists(pkg: str, args: list, config: Config):
    """Checks if a package exists"""

    if "local" in args:
        return os.path.exists(pkg)

    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read()).get("packages", [])

    case = False
    full_match = "full-match" in args
    query = pkg
    if "case" in args:
        case = True
    else:
        query = pkg.lower()

    for package in packages_data:
        name = package.get("name", "")
        n = name
        if not case: n = name.lower()

        res = query in n if not full_match else query == n
        
        if res: return True

    return False

def package_installed(pkg: str, args: list, config: Config):
    """Checks if a package is installed"""
    dpkgs, _, __, ___, _____, ______ = get_all_packages(config)

    case = False
    full_match = "full-match" in args
    query = pkg
    if "case" in args:
        case = True
    else:
        query = pkg.lower()

    for package in dpkgs:
        n = package
        if not case: n = package.lower()

        res = query in n if not full_match else query == n
        
        if res: return True

    return False

def search_packages(queries: list, args: list, config: Config):
    """Searches for a package but via multiple queries"""
    new_item("Searching for packages")
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")

    update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read()).get("packages", [])
    
    printed = 0
    if "all" in args:
        jump("Searching all packages")
        for package in packages_data:
            name = package.get("name", "")
            printed += 1
            step(f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:", color="green", bold=True)
            step_desc(package.get("description", "<No Description>"), color="green", bold=False)
        if printed == 0:
            step("No Packages found!", status="Warning", color="yellow", bold=True)
        return None
    else:
        jump(f"Searching using queries {", ".join(queries)}")

    for package in packages_data:
        name = package.get("name", "")
        for query in queries:
            q = query if "case" in args else query.lower()
            n = name if "case" in args else name.lower()
            if q in n:
                printed += 1
                step(f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:", color="green", bold=True)
                step_desc(package.get("description", "<No Description>"), color="green", bold=False)

    if printed == 0:
        step("No Packages found!", status="Warning", color="yellow", bold=True)

def search_package(query: str, args: list, config: Config):
    """Searches for a package but via single queries"""
    new_item("Searching for package")

    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")

    update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read()).get("packages", [])

    printed = 0
    if "all" in args:
        jump("Searching all packages")
        for package in packages_data:
            name = package.get("name", "")
            printed += 1
            step(f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:", color="green", bold=True)
            step_desc(package.get("description", "<No Description>"), color="green", bold=False)
        if printed == 0:
            step("No Packages found!", status="Warning", color="yellow", bold=True)
        return None
    else:
        jump(f"Searching using query {query}")

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
            printed += 1
            step(f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:", color="green", bold=True)
            step_desc(package.get("description", "<No Description>"), color="green", bold=False)

    if printed == 0:
        step("No Packages found!", status="Warning", color="yellow", bold=True)

# def resolve_dependencies(pkg, visited=None, stack=None):
#     if visited is None:
#         visited = set()
#     if stack is None:
#         stack = set()

#     if pkg in stack:
#         error(f"Dependency cycle detected: {pkg}")
#         return None # Force quit

#     if pkg in visited:
#         return []
    
#     stack.add(pkg)

#     metadata = load_nfx_metadata(pkg)
#     if not metadata:
#         stack.remove(pkg)
#         return []
#     deps = metadata.get("Dependencies", [])

#     order = []
#     for dep in deps:
#         order.extend(resolve_dependencies(dep, visited, stack))

#     stack.remove(pkg)
#     visited.add(pkg)

#     if pkg not in order:
#         order.append(pkg)

#     return order

# def build_install_plan(targets:list):
#     visited = set()
#     plan = []

#     for pkg in targets:
#         plan.extend(resolve_dependencies(pkg, visited=visited))

#     seen = set()
#     final = []

#     for p in plan:
#         if p not in seen:
#             final.append(p)
#             seen.add(p)

#     return final

def install_package(package: str, args: list, config: Config):
    """Installs a package"""
    new_item(f"Installing {package}")

    jump(f"Setting and Checking Directories")
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

    update_packages([], config)

    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read()).get("packages", [])

    exist_args = ["case", "full-match"]
    if "local" in args:
        exist_args.append("local")
    if not package_exists(package, exist_args, config):
        error(f"No such package exists!")
        return None
    elif package_installed(package, ["case", "full-match"], config):
        step(f"Package already installed, use 'upgrade' instead!", status="Warning", color="yellow", bold=True)
        return None

    # fetch repo
    jump(f"Fetching")
    repo_path = fetch_repo(package, cache_dir, "local" not in args, package_data)
    if not repo_path: return None
    
    # load nfx.json
    jump(f"Loading Metadata")
    metadata = load_nfx_metadata(repo_path)
    if not metadata: return None
    metadata["DownloadPath"] = copy_to_downloads(repo_path, download_dir, metadata.get("Name", ""))

    jump(f"Checking Conflicts")
    for conflict in metadata.get("Conflicts", []):
        if package_installed(conflict, ["case", "full-match"], config):
            error(f"Could not install package since it conflicts with installed '{conflict}'")
            return None

    jump(f"Checking Dependencies")
    dependencies = metadata.get("Dependencies", [])
    if len(dependencies) > 0:
        for package in dependencies:
            if package_exists(package, ["case", "full-match"], config) != True:
                error(f"No such package exists: {package}")
                return None

        MAX_THREADS = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = executor.map(
                lambda _pkg_: fetch_repo(_pkg_, cache_dir, "local" not in args, package_data),
                dependencies
            )

        for pkg in dependencies:
            install_package(pkg, args, config)

        new_item(f"Continuing Installation of {package}")

    jump(f"Verifying Dependencies")
    for dep in dependencies:
        if not package_installed(dep, ["case", "full-match"], config):
            error(f"Could not install package since dependency '{dep}' is not installed")
            return None

    # Do verification tests
    jump(f"Verifying")
    if not verify_package(repo_path, cache_dir, metadata, config):
        error("Could not install package since verification failed")
        return None
    
    # run post install scripts from main package
    jump(f"Running Post Install Scripts")
    if metadata.get("PostInstall"):
        step(f"Running post-install script: {metadata['PostInstall']}", status="Log")
        if not run_post_install(os.path.join(metadata["DownloadPath"], metadata.get("PostInstall", []))): return None
    
    # install binaries
    jump(f"Installing Binaries")
    if not install_binaries(metadata, install_dir): return None

    jump(f"Finishing Installation")
    finish_download(metadata.get("Name", ""), metadata)
    
    step(f"Package '{repo_path}' installed successfully!", color="green", bold=True)

def remove_package(args: list, config: Config, name: str):
    new_item(f"Removing {name}")

    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    jump(f"Checking Package details")
    if not os.path.exists(os.path.join(download_dir, name)):
        error("Package was not found in system!")
        return None

    jump(f"Loading Metadata")
    metadata = load_nfx_metadata(os.path.join(download_dir, name))
    if not metadata: return None
    
    jump(f"Removing Binaries")
    if not remove_binaries(metadata, install_dir): return None
    jump(f"Removing package")
    shutil.rmtree(os.path.join(download_dir, name))

    step(f"Package '{name}' removed successfully!", color="green", bold=True)

def upgrade_package(package: str, args: list, config: Config):
    """Updates a package"""
    new_item(f"Upgrading {package}")

    jump(f"Setting and Checking Directories")
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
    
    update_packages([], config)

    if "local" in args:
        new_item("Taking Input")
        # just remove and reinstall
        step("Reinstall local package (y/N): ", status="Input", color="yellow", bold=True)
        if input("").lower() not in ("y", "yes", "yeah", "yea"):
            error("Terminating Upgrade of package", status="Action")
            return None
        step("Please specify proper name of package: ", status="Input", color="yellow", bold=True)
        name = input("")
        remove_package(args, config, name)
        return install_package(package, args, config)

    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read()).get("packages", [])

    if not package_installed(package, ["case", "full-match"], config):
        error(f"No such package found in system!")
        return None

    found = False
    for p in package_data:
        name = p.get("name", "")
        if package == name:
            found = True
            date_obj = datetime.strptime(p.get("update", "1970-01-01 00:00"), "%Y-%m-%d %H:%M")
            md = load_nfx_metadata(os.path.join(download_dir, package))
            date_obj2 = datetime.strptime(md.get("Build", {}).get("Date", "1970-01-01 00:00"), "%Y-%m-%d %H:%M")
            if date_obj > date_obj2:
                remove_package([], config, package)
                if os.path.exists(os.path.join(cache_dir, package + ".zip")):
                    os.remove(os.path.join(cache_dir, package + ".zip"))
                if os.path.exists(os.path.join(cache_dir, package + ".zip.sig")):
                    os.remove(os.path.join(cache_dir, package + ".zip.sig"))
            elif date_obj == date_obj2:
                step("Package is up to date", color="green", bold=True)
                return None
            else:
                eerror("Package/Package_List data is corrupted!")

            new_item(f"Continuing Upgrade of {package}")   
            break

    if not found:
        error(f"No such package found in system: {package}")
        return None

    # fetch repo
    jump(f"Fetching")
    repo_path = fetch_repo(package, cache_dir, "local" not in args, package_data)
    if not repo_path: return None

    # load nfx.json
    jump(f"Loading Metadata")
    metadata = load_nfx_metadata(repo_path)
    if not metadata: return None
    metadata["DownloadPath"] = copy_to_downloads(repo_path, download_dir, metadata.get("Name", ""))

    jump(f"Checking Conflicts")
    for conflict in metadata.get("Conflicts", []):
        if package_installed(conflict, ["case", "full-match"], config):
            error(f"Could not install package since it conflicts with installed '{conflict}'")
            return None

    jump(f"Checking Dependencies")
    dependencies = metadata.get("Dependencies", [])
    if len(dependencies) > 0:
        for package in dependencies:
            if package_exists(package, ["case", "full-match"], config) != True:
                error(f"No such package exists: {package}")
                return None

        MAX_THREADS = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = executor.map(
                lambda _pkg_: fetch_repo(_pkg_, cache_dir, "local" not in args, package_data),
                dependencies
            )

        for pkg in dependencies:
            install_package(pkg, args, config)

        new_item(f"Continuing Installation of {package}")

    jump(f"Verifying Dependencies")
    for dep in dependencies:
        if not package_installed(dep, ["case", "full-match"], config):
            error(f"Could not install package since dependency '{dep}' is not installed")
            return None

    # Do verification tests
    jump(f"Verifying")
    if not verify_package(repo_path, cache_dir, metadata, config):
        error("Could not install package since verification failed")
        return None
    
    # run post install scripts from main package
    jump(f"Running Post Install Scripts")
    if metadata.get("PostInstall"):
        step(f"Running post-install script: {metadata['PostInstall']}", status="Log")
        if not run_post_install(os.path.join(metadata["DownloadPath"], metadata.get("PostInstall", []))): return None
    
    # install binaries
    jump(f"Installing Binaries")
    if not install_binaries(metadata, install_dir): return None

    jump(f"Finishing Installation")
    finish_download(metadata.get("Name", ""), metadata)
    
    step(f"Package '{repo_path}' upgraded successfully!", color="green", bold=True)

def info_package(name: str, args: list, config: Config) -> tuple[dict, str]:
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    if not os.path.exists(os.path.join(download_dir, name)):
        eerror(f"Package '{name}' was not found in cache")

    metadata = load_nfx_metadata(os.path.join(download_dir, name))
    return metadata, os.path.join(download_dir, name)

def install_packages(packages: list, args: list, config: Config):
    new_item("Installing Packages")

    jump("Checking and Setting directories")
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
    
    update_packages([], config)

    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read()).get("packages", [])

    jump("Checking Packages")
    for package in packages:
        if not package_exists(package, ["case", "full-match"], config):
            error(f"No such package exists: {package}")
            return None
        elif package_installed(package, ["case", "full-match"], config):
            step(f"Package already installed: {package} try using 'upgrades' instead (skipping)", status="Warning", color="yellow", bold=True)
            packages.pop(packages.index(package))
    mthreads = 4
    if "thread=" in args:
        for arg in args:
            if "thread=" in arg:
                v:str = arg.replace("thread=", "")
                if not v.isdigit():
                    step_nitem("Provide a number in argument 'threads', defaulting to 4", status="Warning", color="yellow", bold=True)
                else:
                    mthreads = int(v)

    valid_packages = []
    results = None
    
    jump("Fetching Packages")
    cli.Cursor.HideCursor()
    with concurrent.futures.ThreadPoolExecutor(max_workers=mthreads) as executor:
        results = executor.map(
            lambda _pkg_: fetch_repo(_pkg_, cache_dir, "local" not in args, package_data, ConcurProgressBar),
            packages
        )

    cli.Cursor.ShowCusor()
    packages_cpy = packages.copy()
    for pkg, ok in zip(packages_cpy, results):
        if not ok:
            step_nitem(f"Package '{pkg}' failed to fetch properly, skipping...", status="Warning", color="yellow", bold=True)
        else:
                valid_packages.append(pkg)

    jump("Installing")
    for pkg in valid_packages:
        install_package(pkg, args, config)

def upgrade_packages(packages: list, args: list, config: Config):
    for pkg in packages: # cant do parallel here
        upgrade_package(pkg, args, config)

def remove_packages(packages: list, args: list, config: Config):
    for pkg in packages: # cant do parallel here
        remove_package(args, config, pkg)

def enable_winterminal():
    import sys
    if sys.platform.startswith('win'):
        try:
            import ctypes, wintypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.SetConsoleMode.restype = wintypes.BOOL
            kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
            kernel32.GetStdHandle.restype = wintypes.HANDLE
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass    
            
