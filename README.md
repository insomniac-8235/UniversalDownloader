# 📥 Universal DownloaderApp
**v0.1-beta**

A lightweight, high-performance media archiving tool for Windows. Built with Python and CustomTkinter, utilizing the powerful `yt-dlp` engine for high-quality processing.

---

## ✨ Features
* **Modern UI:** Minimalist design with "ghost" input fields.
* **Format Choice:** Toggle between Video or Audio-only (MP3) downloads.
* **Standalone:** No complex setup required once compiled.

---

## 🚀 Installation & Usage

### For Users
1. Go to the **Actions** tab in this repository.
2. Select the latest successful build.
3. Download the `UniversalDownloader-Windows` artifact.

### For Developers
1. Clone the repo: `git clone https://github.com/insomniac-8235/Universal-Downloader.git`
2. Install requirements: `pip install -r requirements.txt`
3. Run: `python main.py`

---

## 🛠️ Build Logic
This project uses **GitHub Actions** to automatically compile the `.exe` on every push to `main`. 

To build manually:
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --collect-all customtkinter main.py

```

---

## ⚖️ Credits

* **Engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* **UI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
