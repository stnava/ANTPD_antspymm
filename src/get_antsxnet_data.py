#!/usr/bin/env python3
"""
Robust downloader for:
- PyMM models (Figshare)
- SIQ super-resolution models (Figshare)
- ANTsXNet data
- ANTsXNet pretrained networks

Features:
- Retries with backoff
- Timeouts
- Atomic downloads
- Corrupt zip detection
- Per-item failure handling
- Skips existing files
"""

import sys
import os
import zipfile
import urllib.request
import urllib.error
import time
import tempfile
import traceback

import antspynet

# ----------------------------- CONFIG -----------------------------

DOWNLOAD_TIMEOUT = 30          # seconds
RETRIES = 3
BACKOFF = 5                    # seconds between retries

# ----------------------------- UTILITIES -----------------------------

def log(msg):
    print(msg, flush=True)

def robust_urlretrieve(url, target_path, retries=RETRIES, timeout=DOWNLOAD_TIMEOUT):
    """
    Download with retries, timeout, and atomic file replacement.
    """
    if os.path.exists(target_path):
        log(f"✅ Already exists, skipping: {target_path}")
        return True

    for attempt in range(1, retries + 1):
        try:
            log(f"⬇️  Downloading (attempt {attempt}/{retries}): {url}")
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            with urllib.request.urlopen(url, timeout=timeout) as response, open(tmp_path, "wb") as out:
                out.write(response.read())

            os.replace(tmp_path, target_path)
            return True

        except Exception as e:
            log(f"❌ Download failed: {e}")
            if attempt < retries:
                time.sleep(BACKOFF * attempt)
            else:
                log(f"❌ FINAL FAILURE: {url}")
                return False

def safe_unzip(zip_path, target_dir):
    """
    Safely extract zip and detect corruption.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            bad = z.testzip()
            if bad:
                raise zipfile.BadZipFile(f"Corrupt file detected: {bad}")
            z.extractall(target_dir)
        return True
    except Exception as e:
        log(f"❌ ZIP extraction failed: {e}")
        return False

# ----------------------------- PYMM -----------------------------

def download_pymm():
    target_dirs = [
        os.path.expanduser("~/.antspyt1w/"),
        os.path.expanduser("~/.antspymm/")
    ]

    figshare_urls = [
        "https://ndownloader.figshare.com/articles/14766102/versions/46",
        "https://figshare.com/ndownloader/articles/16912366/versions/25"
    ]

    for url, target_dir in zip(figshare_urls, target_dirs):
        try:
            os.makedirs(target_dir, exist_ok=True)
            zip_path = os.path.join(target_dir, "pymm_models.zip")

            log(f"\n=== PyMM → {target_dir} ===")

            ok = robust_urlretrieve(url, zip_path)
            if not ok:
                continue

            ok = safe_unzip(zip_path, target_dir)
            if ok:
                os.remove(zip_path)
                log("✅ PyMM extracted successfully.")
            else:
                log("⚠️  PyMM zip kept for inspection.")

        except Exception as e:
            log(f"❌ PyMM FAILED for {target_dir}: {e}")
            traceback.print_exc()

# ----------------------------- SIQ -----------------------------
def download_siq_superres_models(target_dir):
    """
    Robust SIQ downloader:
    - Retries on failure
    - Avoids corrupt partial downloads
    - Prevents pipeline crash
    """

    import time
    import tempfile
    import urllib.request
    import zipfile

    figshare_url = "https://figshare.com/ndownloader/articles/30787214/versions/1"
    target_zip_path = os.path.join(target_dir, "siq_superres_models.zip")

    os.makedirs(target_dir, exist_ok=True)

    MAX_RETRIES = 3
    TIMEOUT = 30

    print(f"\n=== SIQ Super-Resolution Downloader ===")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"⬇️  Attempt {attempt}/{MAX_RETRIES}: {figshare_url}")

            # Download to temp file first (prevents corruption)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            with urllib.request.urlopen(figshare_url, timeout=TIMEOUT) as r, open(tmp_path, "wb") as f:
                f.write(r.read())

            # Atomic replace after full download
            os.replace(tmp_path, target_zip_path)

            # Validate zip before extracting
            with zipfile.ZipFile(target_zip_path, 'r') as zip_ref:
                bad = zip_ref.testzip()
                if bad:
                    raise zipfile.BadZipFile(f"Corrupt file detected: {bad}")
                zip_ref.extractall(target_dir)

            os.remove(target_zip_path)

            print("✅ SIQ models downloaded and extracted successfully.")
            return

        except Exception as e:
            print(f"❌ SIQ attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                time.sleep(5 * attempt)
            else:
                print("❌ FINAL FAILURE: SIQ models could not be downloaded.")
                print("⚠️  Continuing without SIQ (pipeline NOT stopped).")
                return


# ----------------------------- ANTsXNet DATA -----------------------------

def download_antsxnet_data(output_dir, list_file=None):
    data_path = os.path.join(output_dir, "ANTsXNet")
    os.makedirs(data_path, exist_ok=True)

    antspynet.set_antsxnet_cache_directory(data_path)

    if list_file:
        with open(list_file) as f:
            all_data = f.read().splitlines()
    else:
        all_data = list(antspynet.get_antsxnet_data("show"))
        all_data = [x for x in all_data if x != "show"]

    log(f"\n=== Downloading {len(all_data)} ANTsXNet data entries ===")

    failures = []

    for entry in all_data:
        try:
            log(f"⬇️  Data: {entry}")
            antspynet.get_antsxnet_data(entry)
        except Exception as e:
            log(f"❌ FAILED data '{entry}': {e}")
            failures.append(entry)

    if failures:
        log("\n⚠️  These ANTsXNet data downloads failed:")
        for f in failures:
            log(f"  - {f}")

# ----------------------------- PRETRAINED NETWORKS -----------------------------

def download_pretrained_networks(list_file=None):
    if list_file:
        with open(list_file) as f:
            all_networks = f.read().splitlines()
    else:
        all_networks = list(antspynet.get_pretrained_network("show"))
        excludes = {
            'allen_brain_leftright_coronal_mask_weights',
            'allen_cerebellum_coronal_mask_weights',
            'allen_cerebellum_sagittal_mask_weights',
            'allen_sr_weights',
            'show'
        }
        all_networks = [n for n in all_networks if n not in excludes]

    log(f"\n=== Downloading {len(all_networks)} pretrained networks ===")

    failures = []

    for entry in all_networks:
        try:
            log(f"⬇️  Network: {entry}")
            antspynet.get_pretrained_network(entry)
        except Exception as e:
            log(f"❌ FAILED network '{entry}': {e}")
            failures.append(entry)

    if failures:
        log("\n⚠️  These pretrained downloads failed:")
        for f in failures:
            log(f"  - {f}")

# ----------------------------- MAIN -----------------------------

def main():
    if len(sys.argv) == 1:
        print(f"""
Usage:
  {sys.argv[0]} /abs/path/to/ANTsXNetData [doInstall=1] [dataList.txt] [networkList.txt]
""")
        sys.exit(1)

    output_dir = os.path.abspath(sys.argv[1])
    os.makedirs(output_dir, exist_ok=True)

    do_install = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    if do_install == 0:
        log("Installation disabled.")
        sys.exit(0)

    data_list_file = sys.argv[3] if len(sys.argv) > 3 else None
    network_list_file = sys.argv[4] if len(sys.argv) > 4 else None

    log("\n==============================")
    log(" ANTsXNet Robust Downloader ")
    log("==============================\n")

    download_siq_superres_models(output_dir)
    download_pymm()
    download_antsxnet_data(output_dir, data_list_file)
    download_pretrained_networks(network_list_file)

    log("\n✅ ALL DOWNLOAD TASKS COMPLETED.\n")

if __name__ == "__main__":
    main()