import os
import time
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
from tkinter import Tk, filedialog
from bs4 import BeautifulSoup
import re
import json
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.archives13.fr/",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

def extract_info_json_url(page_url):
    r = requests.get(page_url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    for script in soup.find_all('script'):
        script_content = script.string or script.get_text()
        if 'manifestUrl' in script_content:
            manifest_match = re.search(r'"manifestUrl"\s*:\s*"([^"]+)"', script_content)
            if manifest_match:
                manifest_url = manifest_match.group(1).replace('\/', '/')
                return manifest_url

    raise RuntimeError("Could not find IIIF viewer data in the HTML.")

def extract_all_canvas_info_urls(manifest_url):
    print(f"Resolved manifest URL: {manifest_url}")
    manifest_response = requests.get(manifest_url, headers=HEADERS)
    manifest_response.raise_for_status()
    manifest = manifest_response.json()

    info_urls = []
    labels = []

    try:
        if 'items' in manifest:  # IIIF v3.0
            for canvas in manifest['items']:
                image_service_id = canvas['items'][0]['items'][0]['body']['service'][0]['@id']
                label = canvas.get('label', {}).get('none', [f"page_{len(info_urls)+1}"])[0]
                info_urls.append(image_service_id)
                labels.append(label)
        else:  # IIIF v2.0 fallback
            for canvas in manifest['sequences'][0]['canvases']:
                image_service_id = canvas['images'][0]['resource']['service']['@id']
                label = canvas.get('label', f"page_{len(info_urls)+1}")
                info_urls.append(image_service_id)
                labels.append(label)
        return list(zip(info_urls, labels))
    except Exception as e:
        raise RuntimeError(f"Could not extract canvas image info URLs: {e}")

def get_tile_info(info_base_url):
    iiif_url = info_base_url + "/info.json"
    r = requests.get(iiif_url, headers=HEADERS)
    if r.status_code != 200 or not r.content.strip():
        raise RuntimeError(f"Invalid response from {iiif_url}")
    try:
        return r.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON decode error from {iiif_url}: {e}")

def download_cropped_image(info_base_url, output_path):
    info = get_tile_info(info_base_url)
    base_url = info['@id']
    width = info.get('width')
    height = info.get('height')

    if not width or not height:
        raise RuntimeError("Invalid image dimensions in info.json")

    target_width = 7000
    scale_factor = target_width / width
    target_height = int(height * scale_factor)

    region = f"full/{target_width},{target_height}/0/native.jpg"
    image_url = f"{base_url}/{region}"

    r = requests.get(image_url, headers=HEADERS)
    r.raise_for_status()
    image = Image.open(BytesIO(r.content))
    image.save(output_path)

def main():
    import logging
    from datetime import datetime

    page_url = input("Enter your archives page URL: ").strip()
    try:
        manifest_url = extract_info_json_url(page_url)
        info_data = extract_all_canvas_info_urls(manifest_url)
    except Exception as e:
        print(f"Error resolving IIIF info URLs: {e}")
        return

    print("Choose your output folder:")
    Tk().withdraw()
    selected_folder = filedialog.askdirectory(title="Select export folder")
    if not selected_folder:
        print("No folder selected. Exiting.")
        return

    output_dir = Path(selected_folder)
    log_file = output_dir / "Archivesligeo_log.txt"
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(message)s')

    total_start = time.time()

    for i, (info_base_url, label) in enumerate(tqdm(info_data, desc="Downloading pages"), start=1):
        parsed = urlparse(info_base_url)
        name = Path(parsed.path).stem
        safe_label = re.sub(r'[^\w\-_\. ]', '_', label)
        output_path = output_dir / f"{i:03d}_{safe_label}.jpg"

        try:
            page_start = time.time()
            download_cropped_image(info_base_url, output_path)
            elapsed = time.time() - page_start
            print(f"Downloaded page {i} in {elapsed:.2f}s")
            logging.info(f"Downloaded page {i} ({label}) in {elapsed:.2f}s")
        except Exception as e:
            print(f"Error downloading page {i}: {e}")
            logging.error(f"Error downloading page {i}: {e}")

    total_elapsed = time.time() - total_start
    print(f"All done in {total_elapsed:.2f}s")
    logging.info(f"Completed download in {total_elapsed:.2f}s")

if __name__ == '__main__':
    main()
