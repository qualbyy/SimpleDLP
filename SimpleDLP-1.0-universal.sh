#!/bin/bash

SCRIPTDIR=$(dirname "$(readlink -f "$0")")
YTDLPPATH=/usr/local/bin/yt-dlp

# Detect package manager (apt for Ubuntu/Debian/Mint, pacman for Arch)
detect_pm() {
  if command -v apt &>/dev/null; then
    echo "apt"
  elif command -v pacman &>/dev/null; then
    echo "pacman"
  else
    echo "manual"
  fi
}

command_exists() {
  command -v "$1" &> /dev/null
}

can_sudo() {
  sudo -v &> /dev/null
  return $?
}

install_if_missing() {
  cmd=$1
  pm=$(detect_pm)
  if ! command_exists "$cmd"; then
    echo "Command $cmd not found."
    if [ "$pm" = "apt" ] && command_exists sudo && can_sudo; then
      echo "Trying to install $cmd using apt..."
      sudo apt update && sudo apt install -y "$cmd"
    elif [ "$pm" = "pacman" ] && command_exists sudo && can_sudo; then
      echo "Trying to install $cmd using pacman..."
      sudo pacman -S --noconfirm "$cmd"
    else
      echo "No permission or package manager for automatic install."
      echo "Please install $cmd manually for correct functionality."
    fi
  fi
}

ensure_yt_dlp() {
  if ! [ -x "$YTDLPPATH" ]; then
    if command_exists sudo && can_sudo; then
      echo "Downloading yt-dlp..."
      sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o "$YTDLPPATH"
      sudo chmod a+rx "$YTDLPPATH"
    else
      echo "Insufficient permissions for automatic yt-dlp download."
      echo "Please download yt-dlp manually: https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
      echo "Place it at $YTDLPPATH and make it executable."
      exit 1
    fi
  fi
  echo "yt-dlp is ready."
}

echo "Choose an action:"
echo "1 - Stream"
echo "2 - Video"
read -p "Enter 1 or 2: " choice

if [ "$choice" = "1" ]; then
  install_if_missing streamlink
  install_if_missing ffmpeg
  mkdir -p "$SCRIPTDIR/vods"
  read -p "Enter stream URL: " STREAMURL
  streamlink --hls-live-restart "$STREAMURL" best -O | ffmpeg -i - -c copy "$SCRIPTDIR/vods/stream.mp4"
elif [ "$choice" = "2" ]; then
  install_if_missing ffmpeg
  ensure_yt_dlp
  OUTPUTDIR="$SCRIPTDIR/videos"
  mkdir -p "$OUTPUTDIR"
  read -p "Enter video URL: " VIDEOURL
  read -p "If video is restricted, enter path to cookies.txt (or press Enter if not needed): " COOKIESPATH
  if [ -n "$COOKIESPATH" ]; then
    echo "Using cookies file: $COOKIESPATH"
    "$YTDLPPATH" --cookies "$COOKIESPATH" -f bestvideo+bestaudio --merge-output-format mp4 -o "$OUTPUTDIR/%(title)s.%(ext)s" "$VIDEOURL"
  else
    "$YTDLPPATH" -f bestvideo+bestaudio --merge-output-format mp4 -o "$OUTPUTDIR/%(title)s.%(ext)s" "$VIDEOURL"
  fi
  if [ $? -eq 0 ]; then
    echo "Video downloaded successfully."
  else
    echo "Error downloading video."
    echo "
Instructions for obtaining cookies using the Cookies Editor extension:

- Google Chrome / Chromium:
  1. Install 'EditThisCookie' or 'Cookies Editor' from Chrome Web Store.
  2. Open the video page and log into your account if needed.
  3. Click the extension icon and export cookies as cookies.txt.

- Firefox:
  1. Install 'Cookies Manager+' or 'Cookies Editor'.
  2. Go to the video page and log into your account.
  3. Open the extension and export cookies as cookies.txt.

- Microsoft Edge:
  Similar to Google Chrome, use the 'Cookies Editor' extension from the extensions store.

Save this file and retry, specifying its path."
    exit 1
  fi
else
  echo "Invalid input."
  exit 1
fi

read -p "Press Enter to exit..."
