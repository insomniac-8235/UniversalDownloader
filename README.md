![GitHub release (latest by date)](https://img.shields.io/github/v/release/insomniac-8235/UniversalDownloader)
![GitHub top language](https://img.shields.io/github/languages/top/insomniac-8235/UniversalDownloader)
![GitHub last commit](https://img.shields.io/github/last-commit/insomniac-8235/UniversalDownloader)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/insomniac-8235/UniversalDownloader/build.yml)

# Universal Media Downloader
A powerful, easy-to-use GUI for downloading media from various platforms. A standalone, high-performance media archiving utility for Windows. This project was built as an educational exercise to explore Python GUI development, asynchronous threading, and the integration of external command-line binaries (`yt-dlp`, FFmpeg, Deno) into a single compiled executable.

## Download
Click the link below to get the latest stable version for Windows:

[**Download Latest Windows Executable (win64)**](https://github.com/insomniac-8235/UniversalDownloader/releases/latest)

---

## Features
* **Simple GUI:** Built with CustomTkinter for a modern look.
* **High Quality:** Powered by `yt-dlp` for the best available resolution.
* **Portable:** No installation required—just run the `.exe`.

---

## How to Use
1.  Download the `UniversalDownloader_win64_v0.1.0.exe` from the Releases page.
2.  Double-click to run (Windows may show a "SmartScreen" warning; click 'More Info' -> 'Run Anyway' since it's an unsigned app).
3.  Paste your link and hit Download!

---

##  Technical Features & Learning Outcomes
* **Binary Bundling:** Successfully packed FFmpeg and Deno into a headless PyInstaller executable to handle background processing without triggering system consoles.
* **Anti-Bot Bypass:** Implemented a JavaScript runtime (Deno) to navigate and solve modern web-scraping defenses and extraction blocks.
* **Thread-Safe UI:** Engineered a DPI-aware CustomTkinter interface with a custom fake-logger to safely pass real-time download data from background threads to the main UI loop.
* **Maximum Quality:** Configured format selection to automatically fetch and merge 4K video and high-bitrate audio streams natively.

---

##  Core Technologies
* **Engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* **UI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
* **Media Merging:** [FFmpeg](https://ffmpeg.org/)
* **JS Runtime:** [Deno](https://deno.com/)