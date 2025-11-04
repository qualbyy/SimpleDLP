@echo off
setlocal

REM Set paths to yt-dlp.exe, ffmpeg.exe, and streamlink.exe
set YTDLP=yt-dlp.exe
set FFMPEG=ffmpeg.exe
set STREAMLINK=streamlink.exe

echo SimpleDLP for Windows
echo.
echo 1 - Download Livestream
echo 2 - Download Video
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" goto livestream
if "%choice%"=="2" goto video

echo Invalid choice.
pause
exit /b

:livestream
set /p URL="Enter stream URL: "
if not exist vods mkdir vods
echo Recording with Streamlink and FFmpeg...
%STREAMLINK% --hls-live-restart "%URL%" best -O | %FFMPEG% -i - -c copy "vods\stream.mp4"
echo Done.
pause
exit /b

:video
set /p URL="Enter video URL: "
if not exist videos mkdir videos
set /p COOKIES="If video is restricted, enter full path to cookies.txt (or leave blank): "
if not "%COOKIES%"=="" (
    %YTDLP% --cookies "%COOKIES%" -f bestvideo+bestaudio --merge-output-format mp4 -o "videos/%%(title)s.%%(ext)s" "%URL%"
) else (
    %YTDLP% -f bestvideo+bestaudio --merge-output-format mp4 -o "videos/%%(title)s.%%(ext)s" "%URL%"
)
if %errorlevel%==0 (
    echo Video downloaded successfully.
) else (
    echo Error downloading video. You might need to supply browser cookies.
    echo.
    echo Instructions for cookies:
    echo - Chrome: Install 'Cookies Editor', export cookies from the video page as cookies.txt
    echo - Firefox: Install 'Cookies Editor', export cookies as cookies.txt
)
pause
exit /b
