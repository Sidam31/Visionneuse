import os
import math
import time
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from slugify import slugify
from antenati import AntenatiDownloader
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

# Required headers to avoid 403 errors
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://antenati.cultura.gov.it/",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

# Session with retries
session = requests.Session()
retry = Retry(total=5, backoff_factor=1.5, status_forcelist=[403, 429, 500, 502, 503])
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)

def get_tile_info(base_url):
    info_url = f"{base_url}/info.json"
    r = session.get(info_url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def download_tile(base_url, x, y, tile_w, tile_h):
    region = f"{x},{y},{tile_w},{tile_h}"
    tile_url = f"{base_url}/{region}/full/0/default.jpg"
    r = session.get(tile_url, headers=HEADERS)
    r.raise_for_status()
    return (x, y, Image.open(BytesIO(r.content)))

def download_full_image(base_url, output_path):
    info = get_tile_info(base_url)
    width = info.get('width')
    height = info.get('height')
    tiles = info.get('tiles')

    if not tiles:
        raise ValueError(f"No tiling information in info.json for {base_url}")

    tile_width = tiles[0].get('width')
    tile_height = tiles[0].get('height', tile_width)

    cols = math.ceil(width / tile_width)
    rows = math.ceil(height / tile_height)

    full_image = Image.new('RGB', (width, height))

    def tile_task(row, col):
        x = col * tile_width
        y = row * tile_height
        w = min(tile_width, width - x)
        h = min(tile_height, height - y)
        return download_tile(base_url, x, y, w, h)

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_pos = {
            executor.submit(tile_task, row, col): (row, col)
            for row in range(rows) for col in range(cols)
        }
        for future in as_completed(future_to_pos):
            try:
                x, y, tile = future.result()
                full_image.paste(tile, (x, y))
            except Exception as e:
                row, col = future_to_pos[future]
                print(f"Failed tile at row {row}, col {col}: {e}")

    full_image.save(output_path)

def main():
    url = input("Enter Antenati gallery URL: ").strip()
    start_time = time.time()
    downloader = AntenatiDownloader(url, first=0, last=None)
    canvases = downloader.manifest['sequences'][0]['canvases']

    # Extract parts of the label
    label = downloader.manifest.get('label', '')
    manifest_metadata = {item.get('label'): item.get('value') for item in downloader.manifest.get('metadata', [])}
    typology = manifest_metadata.get('Tipologia', '').lower()
    comune = manifest_metadata.get('Comune', '').lower()
    title = manifest_metadata.get('Titolo', '').lower()
    archive = downloader.manifest.get('label', '').lower()

    parts = filter(None, [archive, comune, typology, title])
    subfolder_name = slugify("-".join(parts))

    output_dir = Path(r"C:\Users\") / subfolder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = output_dir / "download_log.txt"
    success_count = 0
    failure_count = 0
    page_times = []

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Download log for: {url}\n")
        log.write(f"Output folder: {output_dir}\n\n")

        for canvas in canvases:
            base_img_url = canvas['images'][0]['resource']['service']['@id']
            label = slugify(canvas['label']) + ".jpg"
            out_path = output_dir / label
            print(f"Downloading: {label}")
            try:
                time.sleep(1)  # Delay between full image requests
                page_start = time.time()
                download_full_image(base_img_url, out_path)
                page_elapsed = time.time() - page_start
                page_times.append(page_elapsed)
                print(f"Saved to: {out_path} ({page_elapsed:.2f} sec)")
                log.write(f"SUCCESS: {label} in {page_elapsed:.2f} seconds\n")
                success_count += 1
            except Exception as e:
                print(f"FAILED: {label} -> {e}")
                log.write(f"FAILED: {label} -> {e}\n")
                failure_count += 1

        total_elapsed = time.time() - start_time
        avg_page_time = sum(page_times) / len(page_times) if page_times else 0
        minutes, seconds = divmod(int(total_elapsed), 60)

        log.write(f"\nSummary:\n  Successful: {success_count}\n  Failed: {failure_count}\n")
        log.write(f"  Time elapsed: {minutes} minutes, {seconds} seconds\n")
        log.write(f"  Average page time: {avg_page_time:.2f} seconds\n")

    print("\nDownload complete.")
    print(f"Successful: {success_count}, Failed: {failure_count}")
    print(f"Time elapsed: {minutes} minutes, {seconds} seconds")
    print(f"Average page time: {avg_page_time:.2f} seconds")
    print(f"Log saved to: {log_file}")

if __name__ == '__main__':
    main()
