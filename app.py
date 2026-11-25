"""Five Transcript - transcricao local de audio e video."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_NAME = "Five Transcript"
APP_VERSION = "1.0.0"
SUPPORT_CONTACT = "Guilherme Augusto - 17992347622"
SUPPORT_WHATSAPP_URL = "https://wa.me/5517992347622"
SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma",
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg",
}


def resource_path(relative_path: str) -> Path:
    """Resolve assets both from source and from a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def find_ffmpeg() -> str | None:
    bundled = resource_path("assets/ffmpeg/bin/ffmpeg.exe")
    if bundled.is_file():
        return str(bundled)
    return shutil.which("ffmpeg")


def find_local_model() -> Path | None:
    """Return the bundled Whisper model only when it is complete."""
    model_dir = resource_path("models/faster-whisper-small")
    required_files = ("model.bin", "config.json", "tokenizer.json")
    if model_dir.is_dir() and all((model_dir / name).is_file() for name in required_files):
        return model_dir
    return None


class FiveTranscriptApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("840x650")
        self.minsize(700, 540)
        self.configure(bg="#f6f7fb")
        self.selected_file: Path | None = None
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build_ui()
        self.after(100, self._read_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), background="#f6f7fb", foreground="#172033")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), background="#f6f7fb", foreground="#667085")
        style.configure("Body.TLabel", font=("Segoe UI", 10), background="#ffffff", foreground="#344054")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 10), background="#0B5CFF", foreground="white")
        style.map("Accent.TButton", background=[("active", "#0848cb"), ("disabled", "#a9c4ff")])
        style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(12, 8))

        outer = tk.Frame(self, bg="#f6f7fb", padx=28, pady=24)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg="#f6f7fb")
        header.pack(fill="x")
        logo_path = resource_path("assets/logo.png")
        if logo_path.is_file():
            try:
                self.logo_image = tk.PhotoImage(file=str(logo_path))
                shrink = max(1, max(self.logo_image.width(), self.logo_image.height()) // 64)
                if shrink > 1:
                    self.logo_image = self.logo_image.subsample(shrink, shrink)
                tk.Label(header, image=self.logo_image, bg="#f6f7fb").pack(side="left", padx=(0, 12))
            except tk.TclError:
                pass
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Label(outer, text="Transcricao local de audio e video", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 18))

        card = tk.Frame(outer, bg="#ffffff", highlightbackground="#e4e7ec", highlightthickness=1, padx=20, pady=20)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Arquivo selecionado", style="Body.TLabel").pack(anchor="w")
        self.file_label = ttk.Label(card, text="Nenhum arquivo selecionado", style="Subtitle.TLabel", wraplength=720)
        self.file_label.pack(anchor="w", pady=(4, 12))

        buttons = tk.Frame(card, bg="#ffffff")
        buttons.pack(fill="x")
        self.select_button = ttk.Button(buttons, text="Selecionar audio ou video", command=self.select_file, style="Secondary.TButton")
        self.select_button.pack(side="left")
        self.transcribe_button = ttk.Button(buttons, text="Transcrever arquivo", command=self.start_transcription, style="Accent.TButton", state="disabled")
        self.transcribe_button.pack(side="right")

        self.progress = ttk.Progressbar(card, mode="indeterminate")
        self.progress.pack(fill="x", pady=(16, 8))
        self.status = ttk.Label(card, text="Pronto para receber um arquivo.", style="Subtitle.TLabel")
        self.status.pack(anchor="w", pady=(0, 12))
        ttk.Label(card, text="Texto transcrito", style="Body.TLabel").pack(anchor="w", pady=(4, 6))

        text_frame = tk.Frame(card, bg="#ffffff")
        text_frame.pack(fill="both", expand=True)
        self.transcript = tk.Text(text_frame, wrap="word", font=("Segoe UI", 10), relief="solid", borderwidth=1, padx=10, pady=10, height=14)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = tk.Frame(card, bg="#ffffff")
        actions.pack(fill="x", pady=(14, 0))
        self.copy_button = ttk.Button(actions, text="Copiar", command=self.copy_text, style="Secondary.TButton", state="disabled")
        self.copy_button.pack(side="left")
        self.save_button = ttk.Button(actions, text="Salvar TXT", command=self.save_text, style="Secondary.TButton", state="disabled")
        self.save_button.pack(side="left", padx=(8, 0))

        footer = tk.Frame(outer, bg="#f6f7fb")
        footer.pack(fill="x", pady=(14, 0))
        ttk.Label(footer, text="Desenvolvido por Guilherme Augusto", style="Subtitle.TLabel").pack()
        ttk.Label(footer, text=f"Suporte: {SUPPORT_CONTACT}", style="Subtitle.TLabel").pack(pady=(2, 0))
        ttk.Button(footer, text="Falar com o suporte no WhatsApp", command=self.open_support, style="Secondary.TButton").pack(pady=(8, 0))

    def select_file(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        selected = filedialog.askopenfilename(title="Selecionar audio ou video", filetypes=[("Audio e video", patterns), ("Todos os arquivos", "*.*")])
        if not selected:
            return
        path = Path(selected)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(APP_NAME, "Formato nao suportado. Selecione um arquivo de audio ou video valido.")
            return
        self.selected_file = path
        self.file_label.configure(text=str(path))
        self.status.configure(text="Arquivo pronto para transcrever.")
        self.transcribe_button.configure(state="normal")

    def start_transcription(self) -> None:
        if not self.selected_file:
            return
        self._set_busy(True, "Preparando a transcricao local...")
        self.transcript.delete("1.0", "end")
        threading.Thread(target=self._transcribe_worker, args=(self.selected_file,), daemon=True).start()

    def _transcribe_worker(self, source: Path) -> None:
        temporary_wav: Path | None = None
        try:
            from faster_whisper import WhisperModel

            audio_path = source
            if source.suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
                ffmpeg = find_ffmpeg()
                if not ffmpeg:
                    raise RuntimeError("FFmpeg nao foi encontrado. Reinstale o aplicativo ou contate o suporte.")
                descriptor, temporary_name = tempfile.mkstemp(prefix="five-transcript-", suffix=".wav")
                os.close(descriptor)
                temporary_wav = Path(temporary_name)
                command = [ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(temporary_wav)]
                result = subprocess.run(command, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode != 0:
                    raise RuntimeError("Nao foi possivel extrair o audio do video selecionado.")
                audio_path = temporary_wav

            model_dir = find_local_model()
            if not model_dir:
                raise RuntimeError(
                    "O modelo local de transcricao ainda nao foi instalado. "
                    "Execute build.ps1 sem -SkipModelDownload para gerar o pacote completo."
                )
            self.events.put(("status", "Transcrevendo localmente. Isso pode levar alguns minutos..."))
            model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(audio_path), language="pt", vad_filter=True, beam_size=5)
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            if not transcript:
                raise RuntimeError("Nenhuma fala foi identificada no arquivo.")
            self.events.put(("done", transcript))
        except Exception as error:  # surfaced in UI, preserving the app session
            self.events.put(("error", str(error)))
        finally:
            if temporary_wav:
                temporary_wav.unlink(missing_ok=True)

    def _read_events(self) -> None:
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "status":
                    self.status.configure(text=str(value))
                elif event == "done":
                    self.transcript.insert("1.0", str(value))
                    self._set_busy(False, "Transcricao concluida.")
                    self.copy_button.configure(state="normal")
                    self.save_button.configure(state="normal")
                elif event == "error":
                    self._set_busy(False, "Nao foi possivel concluir a transcricao.")
                    messagebox.showerror(APP_NAME, str(value))
        except queue.Empty:
            pass
        self.after(100, self._read_events)

    def _set_busy(self, busy: bool, status: str) -> None:
        self.status.configure(text=status)
        state = "disabled" if busy else "normal"
        self.select_button.configure(state=state)
        self.transcribe_button.configure(state=state if self.selected_file else "disabled")
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()

    def copy_text(self) -> None:
        text = self.transcript.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.configure(text="Texto copiado para a area de transferencia.")

    def open_support(self) -> None:
        """Open the configured support conversation in the default browser."""
        opened = webbrowser.open_new_tab(SUPPORT_WHATSAPP_URL)
        if not opened:
            messagebox.showinfo(APP_NAME, f"Entre em contato com: {SUPPORT_CONTACT}")

    def save_text(self) -> None:
        text = self.transcript.get("1.0", "end-1c")
        filename = f"{self.selected_file.stem if self.selected_file else 'transcricao'}.txt"
        target = filedialog.asksaveasfilename(title="Salvar transcricao", defaultextension=".txt", initialfile=filename, filetypes=[("Arquivo de texto", "*.txt")])
        if target:
            Path(target).write_text(text, encoding="utf-8")
            self.status.configure(text="Arquivo TXT salvo com sucesso.")


if __name__ == "__main__":
    FiveTranscriptApp().mainloop()
