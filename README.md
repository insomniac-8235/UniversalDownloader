#  Universal Media Downloader
**v0.1.0** | Educational Project & Python Showcase

A standalone, high-performance media archiving utility for Windows. This project was built as an educational exercise to explore Python GUI development, asynchronous threading, and the integration of external command-line binaries (`yt-dlp`, FFmpeg, Deno) into a single compiled executable.

---

##  Technical Features & Learning Outcomes
* **Binary Bundling:** Successfully packed FFmpeg and Deno into a headless PyInstaller executable to handle background processing without triggering system consoles.
* **Anti-Bot Bypass:** Implemented a JavaScript runtime (Deno) to navigate and solve modern web-scraping defenses and extraction blocks.
* **Thread-Safe UI:** Engineered a DPI-aware CustomTkinter interface with a custom fake-logger to safely pass real-time download data from background threads to the main UI loop.
* **Maximum Quality:** Configured format selection to automatically fetch and merge 4K video and high-bitrate audio streams natively.

---

##  Installation & Usage

### For Users
1. Go to the **Actions** tab in this repository.
2. Select the latest successful build under "Build Universal Downloader".
3. Download the `UniversalDownloader-Windows.zip` artifact at the bottom of the run summary.
4. Extract and run `UniversalDownloader.exe` (No installation required).

---

##  Developer Setup

If cloning this repository to review or modify the code locally, you must provide your own binaries, as large `.exe` files are intentionally ignored by Git.

1. Clone the repo: 
   ```bash
   git clone [https://github.com/insomniac-8235/Universal-Downloader.git](https://github.com/insomniac-8235/Universal-Downloader.git)

2. Create a virtual environment and install requirements:
    ```bash
    pip install -r requirements.txt

3. **⚠️ Crucial Binary Step:** * Download the Windows builds for `ffmpeg.exe`, `ffprobe.exe`, and `deno.exe`.
        * Place all three executables directly into the `assets/` folder.


4. Run the script:
    ```bash
    python main.py
---

##  CI/CD Build Logic

This project uses **GitHub Actions** to automate the build pipeline. On every push to the `main` branch, the workflow automatically spins up a Windows runner, fetches the necessary unversioned binaries via PowerShell, and compiles the final `.exe`.

To build the executable manually on a local Windows machine:

```bash
pyinstaller --noconsole --onefile --windowed --add-data "assets;assets" --icon="assets/icon.ico" --version-file="version.txt" main.py
```

---

##  Core Technologies

* **Engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* **UI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
* **Media Merging:** [FFmpeg](https://ffmpeg.org/)
* **JS Runtime:** [Deno](https://deno.com/)