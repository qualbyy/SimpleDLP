# SimpleDLP

A modern, user-friendly desktop utility for downloading livestreams and online videos. Features an intuitive graphical interface, language switching (English/Russian), persistent settings, and advanced convenience for everyday downloading!

## Features

- **Download livestreams** (mp4) via [Streamlink](https://streamlink.github.io/) and [ffmpeg](https://ffmpeg.org/)
- **Download videos from popular sites** via [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube, etc.)
- **Works with age- and region-restricted content** (just supply your browser’s cookies)
- **Sleek graphical interface** (CustomTkinter-based, works on Linux and Windows)
- **Launcher shortcut for desktop** (no need for command line—double click and go)
- **Instant language switch** (RU/EN) without restart—interface updates on-the-fly
- **Light, dark, or system themes** for comfortable use day or night
- **Remembers your settings** (quality, language, mode, theme) between sessions
- **Browse and save download log**, quick access to downloads folder
- **Simple folder structure, portable and easy to update**

## Requirements

- `python 3.8+`
- `streamlink`
- `ffmpeg`
- `yt-dlp`
- On Arch/SteamOS: `sudo` and `pacman` (auto-install supported); manual setup required on other platforms
- **All other Python libs auto-install—no extra steps needed**

## Installation

1. **Extract the archive** anywhere, e.g.:
~/Downloads/SimpleDLP/

2. **Install dependencies** (if not already):
For Linux:
sudo pacman -S python ffmpeg streamlink
or use pip for streamlink: pip install streamlink
For Windows:
Click "Update Tools" button (creates bin folder and downloads yt-dlp.exe)
Install [FFMPEG](https://www.gyan.dev/ffmpeg/builds/) and put it in a bin folder

4. **Run the program:**
python gui.py

or use the included desktop shortcut (see below).

4. *(Optional for Windows/Linux)*  
Create/copy the desktop shortcut `.desktop` file to your desktop or `~/.local/share/applications/` and adjust the `Exec=` path if needed.

## Usage

- **Interface is intuitive:**  
- Paste a video or stream URL
- Select stream or video mode  
- Set quality or audio mode as desired  
- Optionally select a cookies file for bypassing restrictions  
- Click to download or record—see the status instantly

- **Language switching:**  
Use the dropdown on top to change between English and Russian instantly.

- **Theme:**  
Select light, dark, or system theme from the dropdown at the top.

### Exporting Cookies for Restricted Videos

1. **Google Chrome / Chromium**  
- Install ‘EditThisCookie’ or ‘Cookies Editor’
- Open the target video and log in
- Export cookies to `cookies.txt`
2. **Firefox**  
- Install ‘Cookies Manager+’ or ‘Cookies Editor’
- Open the video and log in
- Export cookies to `cookies.txt`
3. **Microsoft Edge**  
- Use 'Cookies Editor' from Microsoft Edge Add-ons

Supply this file in the GUI when required.

## Advanced

- Video/stream download and conversion is automated in the background and logs appear in the GUI for easy troubleshooting.
- All settings and your chosen GUI language are remembered between runs.
- ``config.json`` saves your preferences—delete it to start fresh!

## License

MIT

---

**Troubleshooting tips:**  
- If the app complains that a command or dependency is missing, please install it manually using your OS’s package manager.
- Double-check file permissions (`chmod +x`) if shortcuts or scripts won’t execute.
- For detailed error output and logs, run `python <name of script>.py` from the terminal.

---

**Author:**  
YouTube: [@qualby](https://www.youtube.com/@qualby)  
Discord: qualbyyyy  
Telegram: @qualbyy
