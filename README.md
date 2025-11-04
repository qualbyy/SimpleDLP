# SimpleDLP

A simple and convenient utility for downloading livestreams and online videos directly from your terminal. Includes ready-to-use desktop shortcuts.

## Features

- **Download livestreams** in mp4 using [Streamlink](https://streamlink.github.io/) + [ffmpeg](https://ffmpeg.org/)
- **Download videos** from popular sites using [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube, etc.)
- **Bypass regional and age restrictions** using cookies export from your browser
- **Desktop launcher**
  
## Requirements

- `bash`
- `streamlink`
- `ffmpeg`
- `yt-dlp`
- `sudo` and `pacman` (for auto-installation on Arch/SteamOS; manual setup required on other systems)

## Installation

1. **Extract the archive** to a folder, for example:
~/Downloads/SimpleDLP/

2. **Make the script executable:**
chmod +x recorderENG.sh

3. **Copy the .desktop file** to your desktop or to `~/.local/share/applications/`:
4. **Make sure the `Exec=` line** in each shortcut points to the corresponding script path.
5. **Make the shortcuts executable:**
chmod +x simpledlpRU.desktop

## Usage

### Using the Terminal
```./recorderENG.sh```

### Using the Desktop Shortcut

Double-click the shortcut

Follow the terminal prompts:
- Choose mode (Stream or Video)
- Enter the URL
- (If needed) specify a cookies file for restricted videos

## Exporting Cookies to Bypass Restrictions

For videos with age/region restrictions, export your browser cookies:

- **Google Chrome / Chromium**
  - Install 'EditThisCookie' or 'Cookies Editor'
  - Open the target video and log in
  - Export cookies to a `cookies.txt` file
- **Firefox**
  - Install 'Cookies Manager+' or 'Cookies Editor'
  - Open the video and log in
  - Export cookies to `cookies.txt`
- **Microsoft Edge**
  - Use the 'Cookies Editor' extension from Edge Add-ons

## License

MIT

---

**Troubleshooting tips:**  
If the terminal says a command is not found, install it manually via your package manager.  
Check your script and shortcut permissions if they won't run.
