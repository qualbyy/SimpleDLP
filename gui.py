import sys
import subprocess
import os
import threading
import shutil
import urllib.request

def check_and_install_packages():
    """Автоматически ставит customtkinter, если не установлен."""
    try:
        import customtkinter
    except ImportError:
        print("Модуль 'customtkinter' не найден. Попытка установки...")
        try:
            command = [sys.executable, "-m", "pip", "install", "customtkinter"]
            if sys.platform.startswith("linux"):
                command.append("--break-system-packages")
            subprocess.check_call(command)
            print("Модуль 'customtkinter' успешно установлен.")
            print("Перезапуск программы...")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"Ошибка при установке 'customtkinter': {e}")
            input("Не удалось установить модуль. Нажмите Enter для выхода.")
            sys.exit(1)

def download_file(url, path):
    try:
        print(f"Скачиваю {url} ...")
        with urllib.request.urlopen(url) as response, open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(path, 0o755)
        print(f"Скачано в {path}")
        return True
    except Exception as e:
        print(f"Ошибка скачивания {url}: {e}")
        return False

def ensure_bin_tools_linux(bin_dir, ytdlp_path, ffmpeg_path):
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    FFMPEG_URL = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    # yt-dlp
    if not os.path.exists(ytdlp_path):
        os.makedirs(bin_dir, exist_ok=True)
        download_file(YTDLP_URL, ytdlp_path)
    # ffmpeg
    if not os.path.exists(ffmpeg_path):
        os.makedirs(bin_dir, exist_ok=True)
        archive_path = os.path.join(bin_dir, "ffmpeg.tar.xz")
        if download_file(FFMPEG_URL, archive_path):
            import tarfile
            try:
                with tarfile.open(archive_path, "r:xz") as tar:
                    ffmpeg_found = False
                    for member in tar.getmembers():
                        if member.isfile() and member.name.endswith("/ffmpeg"):
                            tar.extract(member, bin_dir)
                            extracted_path = os.path.join(bin_dir, os.path.basename(member.name))
                            shutil.move(extracted_path, ffmpeg_path)
                            os.chmod(ffmpeg_path, 0o755)
                            ffmpeg_found = True
                            break
                    if not ffmpeg_found:
                        print("Не найден бинарник ffmpeg в архиве!")
                os.remove(archive_path)
            except Exception as e:
                print(f"Ошибка при распаковке ffmpeg: {e}")

def ensure_tools(bin_dir, ytdlp_path, ffmpeg_path):
    if sys.platform == "win32":
        # Для Windows: выводим инструкцию
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Manual Download Required",
            (
                "Пожалуйста, скачайте yt-dlp.exe и ffmpeg.exe вручную:\n\n"
                "yt-dlp.exe: https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe\n"
                "ffmpeg.exe: https://www.gyan.dev/ffmpeg/builds/\n\n"
                "Положите их в папку 'bin' рядом с программой."
            )
        )
    else:
        # Linux: автоматическая загрузка
        ensure_bin_tools_linux(bin_dir, ytdlp_path, ffmpeg_path)

def main():
    check_and_install_packages()
    import customtkinter
    from tkinter import messagebox, filedialog

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    # Пути
    SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
    BIN_DIR = os.path.join(SCRIPTDIR, "bin")
    if sys.platform == "win32":
        YTDLPPATH = os.path.join(BIN_DIR, "yt-dlp.exe")
        FFMPEGPATH = os.path.join(BIN_DIR, "ffmpeg.exe")
    else:
        YTDLPPATH = os.path.join(BIN_DIR, "yt-dlp")
        FFMPEGPATH = os.path.join(BIN_DIR, "ffmpeg")
    STREAMLINKPATH = "streamlink"

    # Скачиваем или проверяем yt-dlp и ffmpeg
    ensure_tools(BIN_DIR, YTDLPPATH, FFMPEGPATH)

    current_process = None

    def ensure_dependencies():
        missing_files = []
        if not os.path.exists(YTDLPPATH): missing_files.append(os.path.basename(YTDLPPATH))
        if not os.path.exists(FFMPEGPATH): missing_files.append(os.path.basename(FFMPEGPATH))
        if missing_files:
            messagebox.showerror("Dependency Error", f"Не найдены файлы: {', '.join(missing_files)}\n\nПоместите их в папку 'bin'.")
            return False
        return True

    def append_text(text):
        output_text.configure(state="normal")
        output_text.insert("end", text + "\n")
        output_text.see("end")
        output_text.configure(state="disabled")

    def start_stream():
        threading.Thread(target=_start_stream_task, daemon=True).start()

    def _start_stream_task():
        nonlocal current_process
        if not ensure_dependencies(): return
        stream_url = stream_url_entry.get().strip()
        if not stream_url:
            messagebox.showwarning("Input needed", "Enter stream URL")
            return
        append_text(f"Starting stream download from {stream_url}...")
        stop_button.configure(state="normal")
        vods_dir = os.path.join(SCRIPTDIR, "vods")
        os.makedirs(vods_dir, exist_ok=True)
        cmd = f'"{STREAMLINKPATH}" --hls-live-restart "{stream_url}" best -O | "{FFMPEGPATH}" -i - -c copy "{os.path.join(vods_dir, "stream.mp4")}"'
        current_process = subprocess.Popen(cmd, shell=True)
        append_text("Stream capture started.")
        current_process.wait()
        append_text("Stream capture finished.")
        stop_button.configure(state="disabled")

    def start_video_download_thread():
        threading.Thread(target=_start_video_download_task, daemon=True).start()

    def _start_video_download_task():
        nonlocal current_process
        if not ensure_dependencies(): return
        videos_dir = os.path.join(SCRIPTDIR, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        video_url = video_url_entry.get().strip()
        if not video_url: return
        cookies_path = cookies_path_entry.get().strip()
        append_text(f"Downloading video from {video_url}...")
        stop_button.configure(state="normal")
        cmd_parts = [
            f'"{YTDLPPATH}"', '--ffmpeg-location', f'"{os.path.dirname(FFMPEGPATH)}"',
            '-f', 'bestvideo+bestaudio', '--merge-output-format', 'mp4',
            '-o', f'"{os.path.join(videos_dir, "%(title)s.%(ext)s")}"', f'"{video_url}"'
        ]
        if cookies_path: cmd_parts.insert(1, f'--cookies "{cookies_path}"')
        cmd = " ".join(cmd_parts)
        current_process = subprocess.Popen(cmd, shell=True)
        current_process.wait()
        append_text("Download process finished.")
        stop_button.configure(state="disabled")
        current_process = None

    def stop_download():
        nonlocal current_process
        if current_process and current_process.poll() is None:
            if sys.platform == "win32":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(current_process.pid)])
            else:
                os.killpg(os.getpgid(current_process.pid), 9)
            append_text("Загрузка остановлена.")
        else:
            append_text("Нет активного процесса загрузки.")
        stop_button.configure(state="disabled")
        current_process = None

    def browse_cookies():
        path = filedialog.askopenfilename(title="Select cookies.txt file", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            cookies_path_entry.delete(0, "end")
            cookies_path_entry.insert(0, path)

    # --- CUSTOMTKINTER GUI ---
    class App(customtkinter.CTk):
        def __init__(self):
            super().__init__()
            self.title("SimpleDLP")
            self.geometry("800x600")
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(2, weight=1)

            input_frame = customtkinter.CTkFrame(self)
            input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
            input_frame.grid_columnconfigure(1, weight=1)

            customtkinter.CTkLabel(input_frame, text="Stream URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            nonlocal stream_url_entry
            stream_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            stream_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            customtkinter.CTkLabel(input_frame, text="Video URL:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
            nonlocal video_url_entry
            video_url_entry = customtkinter.CTkEntry(input_frame, placeholder_text="https://...")
            video_url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

            customtkinter.CTkLabel(input_frame, text="Cookies File:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
            nonlocal cookies_path_entry
            cookies_path_entry = customtkinter.CTkEntry(input_frame, placeholder_text="C:/path/to/cookies.txt")
            cookies_path_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
            browse_button = customtkinter.CTkButton(input_frame, text="Browse...", width=80, command=browse_cookies)
            browse_button.grid(row=2, column=2, padx=10, pady=10)

            button_frame = customtkinter.CTkFrame(self)
            button_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
            button_frame.grid_columnconfigure((0, 1), weight=1)

            stream_button = customtkinter.CTkButton(button_frame, text="Download Stream", command=start_stream)
            stream_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

            video_button = customtkinter.CTkButton(button_frame, text="Download Video", command=start_video_download_thread)
            video_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            nonlocal stop_button
            stop_button = customtkinter.CTkButton(button_frame, text="Stop Download", command=stop_download, fg_color="#D32F2F", hover_color="#B71C1C", state="disabled")
            stop_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

            nonlocal output_text
            output_text = customtkinter.CTkTextbox(self, state="disabled")
            output_text.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

    # Глобальные переменные для доступа внутри функций
    stream_url_entry, video_url_entry, cookies_path_entry, stop_button, output_text = None, None, None, None, None

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
