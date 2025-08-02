# Antenati High Quality Downloader - README

This tool downloads high-resolution images from the Antenati website using IIIF tile-based reconstruction.

---

## 🔧 Prerequisites & Installation

Before using this script, make sure you have:

### 1. Python Installed

* Download and install Python (version 3.8 or above): [https://www.python.org/downloads/](https://www.python.org/downloads/)
* During installation, make sure to check **"Add Python to PATH"**.

### 2. Required Python Libraries

Open a terminal or command prompt and navigate to the folder with the script. Run:

```bash
pip install -r requirements.txt
```

This will install:

* `click`
* `python-slugify`
* `humanize`
* `tqdm`
* `requests`
* `pillow` (required separately)

If `pillow` is not installed via `requirements.txt`, install it manually:

```bash
pip install pillow
```

---

## 📁 Setup: Choose Your Output Folder

Before running the script, you must define where you want the downloaded images to be saved.

1. Open the script file `download_hq.pyw` with a text editor (like Notepad++ or VSCode).
2. Look for the line starting with:

```python
output_dir = Path(
```

3. Change the folder path to the one you want. Example:

```python
output_dir = Path(r"C:\Users\YourName\Documents\Antenati Downloads") / subfolder_name
```

> **Make sure to use double backslashes `\\` or prefix the string with `r"..."` when using Windows paths.**

---

## ▶️ How to Use

1. **Double-click** the `download_hq.pyw` file (or run it from terminal).
2. **Open** the registry on Antenati and **Copy** the URL of the Antenati gallery when prompted (example: https://antenati.cultura.gov.it/ark:/12657/an_ua36176/ )
3. Wait as the tool downloads and assembles the high-resolution images.
4. Images will be saved in the folder you defined earlier, in a subfolder named after the archive, comune, typology, and year.

---

## 📄 Output

* Images will be named by page (e.g., `pag-1.jpg`, `pag-2.jpg`, etc.)
* A `download_log.txt` will summarize download results, errors, and timings.

---

## ❓ Need Help?

If you get any errors, check:

* Your internet connection
* That the URL is valid and from Antenati
* That Python and all required libraries are installed

You can also ask for help by sharing the log file.

---

Buona giornata! 🎉
