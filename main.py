import shutil
import tarfile
import tempfile
import zipfile
import re
import requests
import os


def get_package_information(package_name):
    # Gets package info from pypi
    pypi_url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(pypi_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Wasn't able to find:{package_name}. Status code:{response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e} ")
        return None


def get_package_latest_version(package_name):
    # Gets the latest package version from the returned JSON
    package = get_package_information(package_name)
    if package:
        return package["info"]["version"]
    else:
        return None


def download_package(package_name):
    # Downloads the latest version of the package, prioritizing .whl over .tar.gz.
    info = get_package_information(package_name)
    if not info:
        return None

    version = get_package_latest_version(package_name)
    if not version:
        print(f'No available version found for: {package_name}')
        return None

    releases = info["releases"][version]
    download_url = None
    for rel in releases:
        if rel["packagetype"] == "bdist_wheel":
            download_url = rel["url"]
            break

    if not download_url:
        for rel in releases:
            if rel["packagetype"] == "sdist":
                download_url = rel["url"]
                break
    if not download_url:
        print(f"No download URL for .whl or tar.gz was found for {package_name}{version}")
        return None

    # If a URL found the code proceeds to download, makes a temp dir to download the package into
    download_dir = tempfile.mkdtemp()
    print(f"The downloading directory is: {download_dir}")

    try:
        response = requests.get(download_url)

        if response.status_code == 200:
            filename = download_url.split("/")[-1]
            path = str(download_dir) + "/" + str(filename)
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"downloaded to {path}")
            return path, download_dir
        else:
            print(f"Wasn't able to download the package: status{response.status_code}")
            return None, download_dir

    except Exception as e:
        print(f"Wasn't able to download the package: {e}")
        return None, download_dir


def extract_file(path, download_dir):
    # Extracts the downloaded file to a directory.
    extract_dir = str(download_dir) + "extracted"
    os.makedirs(extract_dir)
    # Uses zipfile to extract .whl files and tarfile to extract .tar.gz files
    try:
        if path.endswith(".whl"):
            with zipfile.ZipFile(path, "r") as zip:
                zip.extractall(extract_dir)
                print(f"extracted .whl file to {extract_dir}")
        elif path.endswith(".tar.gz"):
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(extract_dir)
                print(f"extracted tar.gz file to {extract_dir}")
        else:
            print(f"the file format of {path} isn't supported")
            return None
        return extract_dir
    except Exception as e:
        print(f"Wasn't able to extract file : {e}")
        return None


def dependency_extractor(extract_dir):
    # Extracts dependencies from the package metadata.
    dependencies = []

    # for a .whl will look for METADATA file
    metadata_path = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.lower() == "metadata":
                metadata_path = os.path.join(root, 'METADATA')
                break


    # Looks for 'Requires-Dist': to find dependencies

    if metadata_path:
        print(f"found metadata at: {metadata_path}")
        try:
            with open(metadata_path, "r") as f:
                for line in f:
                    if line.startswith("Requires-Dist:"):
                        dependency = line[len("Requires-Dist:"):].strip()
                        dependencies.append(dependency)
        except Exception as e:
            print(f"Error with METADATA: {e}")
    else:
        # Looks for a setup.py
        setuppy_path = None
        for root, _, files in os.walk(extract_dir):
            for f in files:
                if f.lower() == "setup.py":
                    setuppy_path = os.path.join(root, 'setup.py')
                    break

        # Looks for install_requires = [ ... ]
        if setuppy_path:
            print(f"found setup.py at: {setuppy_path}")
            try:
                with open(setuppy_path, "r") as f:
                    content = f.read()
                    match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
                    if match:
                        requires = match.group(1)
                        for line in requires.split(","):
                            line = line.strip()
                            if line.startswith("'") or line.startswith('"'):
                                line = line.strip("'\"")
                            if line:
                                dependencies.append(line)
            except Exception as e:
                print(f"Error with setup.py: {e}")
                # Looks for a requirements.txt if both metadata and setup.py missing
        req_path = None
        for root, _, files in os.walk(extract_dir):
            if "requirements.txt" in files:
                req_path = os.path.join(root, "requirements.txt")
                break

        if req_path:
            print(f"found requirement.txt at {req_path}")
            try:
                with open(req_path, "r") as f:
                    # cleaning up unnecessary lines
                    for line in f:
                        line = line.split("#")[0].strip()
                        if line and not line.startswith("-"):
                            dependencies.append(line)
            except Exception as e:
                print(f"Error with requirements.txt:{e}")

    return dependencies


def package_analyzer(package_name):
    # Analyzes a package, retrieves its version, downloads it, and extracts dependencies.
    print(f"getting information about {package_name}")

    version = get_package_latest_version(package_name)

    if not version:
        print(f"Couldn't find version information for {package_name}")
        return None

    downloaded_package = download_package(package_name)
    if not downloaded_package:
        print(f"Couldn't download {package_name}")
        return None

    path, download_dir = downloaded_package

    try:
        extract_dir = extract_file(path, download_dir)
        if not extract_dir:
            print(f"Couldn't extract {package_name}")
            return None
    except Exception as e:
        print(f"Wasn't able to extract: {e}")
        return None

    dependencies = dependency_extractor(extract_dir)

    result = {
        "Package name": package_name,
        "Version": version,
        "Dependencies": dependencies
    }

    # Removes the temp directories.
    try:
        shutil.rmtree(download_dir)
        #shutil.rmtree(extract_dir)
        print(f"Removed temporary folder: {download_dir} and {extract_dir}")
    except Exception as e:
        print(f"Error removing temp directory: {e}")

    return result
def main():
    package_name = input("Please insert the name of the package you want to get the info for: ")
    result = package_analyzer(package_name)
    if result:
        print(result)
    else:
        print("Failed toa analyze")

if __name__ == "__main__":
    main()


