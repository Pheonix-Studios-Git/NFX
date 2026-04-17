"""Downloading Manager File"""
import subprocess, os, shutil, json, stat, zipfile, time, hashlib
import urllib.request
import concurrent.futures

from phardwareitk.Extensions import *
from phardwareitk.Extensions.HyperOut import *
from src import *
from src.config import *

from src.constants import BASE_DIR_DEF

EXEC = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

PPI_PAGE = "https://pheonix-studios-git.github.io/PPI/data/"

def step(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"    -> {msg:<20} {status_str}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

def jump(msg, status=None, color="white", bold=False):
    status_str = ""
    if status:
        status_str = f"[{status}]"
    printH(f"  :{status_str}: {msg:<20}", FontEnabled=True, Font=TextFont(font_color=Color(color),Bold=bold))

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

def fetch_repo(repo_url:str, cache_dir:str, ppi:bool, package_json:dict) -> str:
    """
    Clone a git repo or copy local path to cache_dir
    Returns path to cloned repo.
    """
    repo_name = os.path.basename(repo_url.rstrip("/")).replace(".zip", "")
    target_path = os.path.join(cache_dir, repo_name)

    if os.path.exists(target_path):
        return target_path

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
            step("Package not found!", status="Error", color="red", bold=True)
            os._exit(-6)
        os.mkdir(target_path)
        zippath = os.path.join(cache_dir, repo_name + ".zip")
        sigpath = os.path.join(cache_dir, repo_name + ".sig")
        if os.path.exists(zippath):
            try:
                with zipfile.ZipFile(zippath, 'r') as zip_ref:
                    zip_ref.extractall(target_path) # Keep downloaded cache
            except zipfile.BadZipFile:
                step(f"Not a valid zip file [{zippath}]", status="Error", color="red", bold=True)
                os.remove(zippath)
                os.rmdir(target_path)
                os._exit(-4)
            except Exception as e:
                step(f"Error Downloading the file '{repo_url + package_json[index].get("zipfile", "Error404NotFound")}' to '{target_path}'", status="Error", color="red", bold=True)
                os.rmdir(target_path)
                step(e, status="Error", color="red", bold=True)
                os._exit(-5)
        else:
            try:
                urllib.request.urlretrieve(repo_url + package_json[index].get("zipfile", "Error404NotFound"), zippath)
                with zipfile.ZipFile(zippath, 'r') as zip_ref:
                    zip_ref.extractall(target_path) # Keep downloaded cache
            except zipfile.BadZipFile:
                step(f"Not a valid zip file [{zippath}]", status="Error", color="red", bold=True)
                os.remove(zippath)
                os.rmdir(target_path)
                os._exit(-4)
            except Exception as e:
                step(f"Error Downloading the file '{repo_url + package_json[index].get("zipfile", "Error404NotFound")}' to '{target_path}'", status="Error", color="red", bold=True)
                os.rmdir(target_path)
                step(e, status="Error", color="red", bold=True)
                os._exit(-5)

            if package_json[index].get("signed_zipfile", "") != "":
                try:
                    urllib.request.urlretrieve(repo_url + package_json[index].get("signed_zipfile", "Error404NotFound"), sigpath)
                except Exception as e:
                    step(f"Error Downloading the file '{repo_url + package_json[index].get("signed_zipfile", "Error404NotFound")}' to '{sigpath}'", status="Error", color="red", bold=True)
                    os.rmdir(target_path)
                    step(e, status="Error", color="red", bold=True)
                    os._exit(-5)

    return target_path

def load_nfx_metadata(repo_path: str) -> dict:
    """Loads nfx file if found in pkg"""
    nfx_file = os.path.join(repo_path, "nfx.json")
    if not os.path.exists(nfx_file):
        step("nfx.json not found!", status="Error", color="red", bold=True)
        os._exit(6)
    with open(nfx_file, "r") as f:
        data = json.load(f)
    return data

def load_nfx_metadata_ex(nfx_file:str) -> dict:
    """Loads NFX MetaData (Extended)"""
    if not os.path.exists(nfx_file):
        step("nfx.json not found!", status="Error", color="red", bold=True)
        os._exit(6)
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
    
def install_binaries(metadata: dict, install_dir: str):
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
            
            if os.path.exists(dest_path):
                os.remove(dest_path)
            
            os.symlink(src_path, dest_path)
            os.chmod(dest_path, os.stat(dest_path).st_mode | EXEC)
            
            if bin_info.get("PostInstall"):
                run_post_install(os.path.join(metadata.get("DownloadPath", ""), bin_info.get("PostInstall", "")))

            downloaded_binaries += 1

    if downloaded_binaries == 0:
        step("The specified package doesn't support the machine! Continuing (Won't Install Binaries)", status="Warning", color="yellow", bold=True)

def remove_binaries(metadata: dict, install_dir: str):
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
            
            os.unlink(dest_path)
            
            deleted_binaries += 1

    if deleted_binaries == 0:
        step("The specified package doesn't support the machine! Continuing (No Binaries were installed in the first place, probably!)", status="Warning", color="yellow", bold=True)

def run_post_install(script_path: str):
    """Runs post install scripts"""
    os.chmod(script_path, os.stat(script_path).st_mode | EXEC)
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        subprocess.run([script_path], check=True)
    else:
        step("Post Install failed to run!", status="Error", color="red", bold=True)
        
def package_exists(pkg: str, args: list, config: Config):
    """Checks if a package exists"""
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    if not os.path.exists(packages_json):
        update_packages(flags, config)

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

def verify_package(repo_path: str, cache_dir: str, metadata: dict):
    "Verifies the package and takes in user input as well, uses ED22519 and SHA256"
    # Verify Zip signature
    repo_name = os.path.basename(repo_path)
    sigpath = os.path.join(cache_dir, repo_name + ".sig")
    zippath = os.path.join(cache_dir, repo_name + ".zip")
    if not os.path.exists(zippath):
        step("Package lost its cached zipfile!", status="Error", color="red", bold=True)
        return False
    if (os.path.exists(sigpath)):
        result = subprocess.run(
            [
                "ssh-keygen",
                "-Y", "verify",
                "-f", metadata.get("Build", {}).get("AllowedSigners", ""),
                "-I", metadata.get("Build", {}).get("SignerIdentity", ""),
                "-n", "file",
                "-s", sigpath,
            ],
            input=open(zippath, "rb").read(),
            capture_output=True,
        )
        if result.returncode != 0:
            step("Package is tampered with (Risk: Very High), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
            if input("").lower() not in ("y", "yes", "yeah", "yea"):
                return False
    else:
        step("Package is unverified with (Risk: High), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
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
            
            if not os.path.exists(src_path):
                step("Package lost its binaries!", status="Error", color="red", bold=True)
                return False
            hash_ = sha256sum_file(src_path)
            if hash_ != bin_info.get("Sha256", 0):
                step("Package has invalid sha256 hashed binaries (Risk: Medium), do you want to continue (y/N): ", status="Input", color="yellow", bold=True)
                if input("").lower() not in ("y", "yes", "yeah", "yea"):
                    return False
    
    return True


def update_packages(args: list, config: Config):
    """Updates the package json file"""
    packages = os.path.join(BASE_DIR_DEF, "packages.json")
    
    try:
        urllib.request.urlretrieve(PPI_PAGE + "packages.json", packages)
    except Exception as e:
        step("Error Downloading Packages List!", status="Error", color="red", bold=True)
        os._exit(-5)

    step("Synced Package List!", color="green", bold=True)

def search_packages(queries: list, args: list, config: Config):
    """Searches for a package but via multiple queries"""
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    if not os.path.exists(packages_json):
        update_packages([], config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read()).get("packages", [])
    
    if "all" in args:
        for package in packages_data:
            name = package.get("name", "")
            printH(
                f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:\n\t{package.get("description", "<No Description>")}",
                FontEnabled=True,
                Font = TextFont(
                    font_color = Color("cyan"),
                    Bold = True
                )
            )
        return None

    for package in packages_data:
        name = package.get("name", "")
        for query in queries:
            q = query if "case" in args else query.lower()
            n = name if "case" in args else name.lower()
            if q in n:
                printH(
                    f"{name} by {package.get("author", "<No Author>")}:\n\t{package.get("description", "No Description")}",
                    FontEnabled=True,
                    Font = TextFont(
                        font_color = Color("cyan"),
                        Bold = True
                    )
                )

def search_package(query: str, args: list, config: Config):
    """Searches for a package but via single queries"""
    packages_json = os.path.join(BASE_DIR_DEF, "packages.json")
    if not os.path.exists(packages_json):
        update_packages(flags, config)

    packages_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        packages_data = json.loads(f.read()).get("packages", [])

    if "all" in args:
        for package in packages_data:
            name = package.get("name", "")
            printH(
                f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:\n\t{package.get("description", "<No Description>")}",
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
                f"{name if name else "<No Name>"} by {package.get("author", "<No Author>")}:\n\t{package.get("description", "<No Description>")}",
                FontEnabled=True,
                Font = TextFont(
                    font_color = Color("cyan"),
                    Bold = True
                )
            )

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
    if not os.path.exists(packages_json):
        update_packages(args, config)

    jump(f"Syncing Package Lists")
    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read()).get("packages", [])

    if package_exists(package, ["case", "full-match"], config) != True:
        step(f"No such package", status="Error", color="red", bold=True)
        return None

    # fetch repo
    jump(f"Fetching")
    repo_path = fetch_repo(package, cache_dir, "local" not in args, package_data)
    
    # load nfx.json
    jump(f"Loading Metadata")
    metadata = load_nfx_metadata(repo_path)
    metadata["DownloadPath"] = copy_to_downloads(repo_path, download_dir, metadata.get("Name", ""))

    jump(f"Checking Conflicts")
    for conflict in metadata.get("Conflicts", []):
        if package_exists(conflict, ["case", "full-match"], config):
            step(f"Could not install package since it conflicts with installed '{conflict}'", status="Error", color="red", bold=True)
            return None

    jump(f"Checking Dependencies")
    dependencies = metadata.get("Dependencies", [])
    if len(dependencies) > 0:
        for package in packages:
            if package_exists(package, ["case", "full-match"], config) != True:
                step(f"No such package: {package}", status="Error", color="red", bold=True)
                return None

        MAX_THREADS = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = executor.map(
                lambda _pkg_: fetch_repo(_pkg_, cache_dir, "local" not in args, package_data),
                packages
            )

        for pkg in packages:
            install_package(pkg, args, config)

        new_item(f"Continuing Installation of {package}")

    jump(f"Verifying Dependencies")
    for dep in dependencies:
        if not package_exists(dep, ["case", "full-match"], config):
            step(f"Could not install package since dependency '{dep}' is not installed", status="Error", color="red", bold=True)
            return None

    # Do verification tests
    jump(f"Verifying")
    if not verify_package(repo_path, cache_dir, metadata):
        step("Could not install package since verification failed", status="Error", color="red", bold=True)
        return None
    
    # run post install scripts from main package
    jump(f"Running Post Install Scripts")
    if metadata.get("PostInstall"):
        step(f"Running post-install script: {metadata['PostInstall']}", status="Log")
        run_post_install(os.path.join(metadata["DownloadPath"], metadata.get("PostInstall", [])))
    
    # install binaries
    jump(f"Installing Binaries")
    install_binaries(metadata, install_dir)

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
        step("Package was not found", status="Error", color="red", bold=True)
        os._exit(-7)

    jump(f"Loading Metadata")
    metadata = load_nfx_metadata(os.path.join(download_dir, name))
    
    jump(f"Removing Binaries")
    remove_binaries(metadata, install_dir)
    jump(f"Removing package")
    shutil.rmtree(os.path.join(download_dir, name))

    step(f"Package '{name}' removed successfully!", color="green", bold=True)

def info_package(name: str, args: list, config: Config) -> tuple[dict, str]:
    download_dir = config.download_dir
    cache_dir = config.cache_dir
    install_dir = config.install_dir

    if not os.path.exists(os.path.join(download_dir, name)):
        printH(f"Package '{name}' was not found in cache", FontEnabled=True, Font=TextFont(font_color=Color("red")))
        os._exit(-7)

    metadata = load_nfx_metadata(os.path.join(download_dir, name))
    return metadata, os.path.join(download_dir, name)

def install_packages(packages: list, args: list, config: Config):
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
        update_packages(args, config)

    package_data = {}
    with open(packages_json, "r") as f:
        f.seek(0)
        package_data = json.loads(f.read()).get("packages", [])

    for package in packages:
        if package_exists(package, ["case", "full-match"], config) != True:
            printH(f"No such package: {package}", FontEnabled=True, Font=TextFont(font_color=Color("red"), Bold=True))
            return None

    MAX_THREADS = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        results = executor.map(
            lambda _pkg_: fetch_repo(_pkg_, cache_dir, "local" not in args, package_data),
            packages
        )

    for pkg in packages:
        install_package(pkg, args, config)

def remove_packages(packages: list, args: list, config: Config):
    MAX_THREADS = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        results = executor.map(
            lambda _pkg_: remove_package(args, config, _pkg_),
            packages
        )

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
            
