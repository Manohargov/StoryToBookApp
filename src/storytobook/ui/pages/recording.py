"""Recording screen: capture or import the spoken story."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...domain.project import ProjectStatus
from ...services.audio import AudioRecorder, list_input_devices, sounddevice_available
from ..theme import COLORS, SIZES, Card, SectionTitle, font, muted_font
from .base import Page

AUDIO_FILETYPES = [
    ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
    ("All files", "*.*"),
]


class RecordingPage(Page):
    """Records from the microphone or imports an existing file."""

    title = "Record"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.recorder: AudioRecorder | None = None
        self._meter_job = None
        self._ticker_job = None
        self.build()

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(30, 0))
        header.grid_columnconfigure(0, weight=1)
        SectionTitle(
            header,
            "Record your story",
            "Speak naturally. Whisper will clean the transcript up afterwards, "
            "and you can edit it before anything is typeset.",
        ).grid(row=0, column=0, sticky="ew")

        self.panel = Card(wrapper)
        self.panel.grid(row=1, column=0, sticky="ew", padx=34, pady=(20, 0))
        self.panel.grid_columnconfigure(0, weight=1)

        # --- device picker -------------------------------------------- #
        device_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        device_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 6))
        device_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            device_row, text="Microphone", font=font(SIZES["small"], "bold"), text_color=COLORS["muted"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))

        self.device_menu = ctk.CTkOptionMenu(
            device_row,
            values=["Default device"],
            width=320,
            height=34,
            corner_radius=8,
            command=self._on_device_change,
        )
        self.device_menu.grid(row=0, column=1, sticky="w")

        self.device_index: int | None = None

        # --- meter ----------------------------------------------------- #
        meter = ctk.CTkFrame(self.panel, fg_color="transparent")
        meter.grid(row=1, column=0, sticky="ew", padx=22, pady=(10, 0))
        meter.grid_columnconfigure(0, weight=1)

        self.timer_label = ctk.CTkLabel(
            meter, text="00:00", font=font(30, "bold"), text_color=COLORS["text"]
        )
        self.timer_label.grid(row=0, column=0, sticky="w")

        self.level_text = ctk.CTkLabel(
            meter, text="", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        )
        self.level_text.grid(row=0, column=1, sticky="e")

        self.level_bar = ctk.CTkProgressBar(meter, height=10, corner_radius=5)
        self.level_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.level_bar.set(0)

        # --- controls -------------------------------------------------- #
        controls = ctk.CTkFrame(self.panel, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=22, pady=(18, 22))

        self.record_button = ctk.CTkButton(
            controls,
            text="Start recording",
            width=190,
            height=44,
            corner_radius=10,
            font=font(SIZES["body"], "bold"),
            fg_color=COLORS["danger"],
            hover_color="#d43f38",
            command=self._toggle_recording,
        )
        self.record_button.pack(side="left")

        self.import_button = ctk.CTkButton(
            controls,
            text="Import audio file",
            width=160,
            height=44,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["surface_alt"],
            command=self._import_audio,
        )
        self.import_button.pack(side="left", padx=10)

        self.manual_button = ctk.CTkButton(
            controls,
            text="Type it instead",
            width=150,
            height=44,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=self._manual_entry,
        )
        self.manual_button.pack(side="left")

        # --- actions --------------------------------------------------- #
        self.actions = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.actions.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 22))

        self.transcribe_button = ctk.CTkButton(
            self.actions,
            text="Transcribe & continue",
            width=220,
            height=44,
            corner_radius=10,
            font=font(SIZES["body"], "bold"),
            state="disabled",
            command=self._transcribe,
        )
        self.transcribe_button.pack(side="left")

        self.hint_label = ctk.CTkLabel(
            self.actions,
            text="",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.hint_label.pack(side="left", padx=12)

        self.progress = ctk.CTkProgressBar(wrapper, height=8, corner_radius=4)
        self.progress.grid(row=3, column=0, sticky="ew", padx=34, pady=(16, 0))
        self.progress.set(0)
        self.progress.grid_remove()

        self.progress_label = ctk.CTkLabel(
            wrapper,
            text="",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.progress_label.grid(row=4, column=0, sticky="ew", padx=34, pady=(6, 0))
        self.progress_label.grid_remove()

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        self._refresh_devices()
        self._sync_project_state()

    def on_hide(self) -> None:
        self._stop_meters()

    # ------------------------------------------------------------------ #
    def _refresh_devices(self) -> None:
        devices = list_input_devices()
        if not devices:
            self.device_menu.configure(values=["No microphone detected"])
            self.device_menu.set("No microphone detected")
            self.hint_label.configure(
                text="Install sounddevice to record, or import an audio file."
            )
            return

        labels = ["Default device"] + [d["name"] for d in devices]
        self.device_menu.configure(values=labels)
        self.device_menu.set(labels[0])
        self._devices = devices

    def _on_device_change(self, choice: str) -> None:
        if choice == "Default device":
            self.device_index = None
            return
        devices = getattr(self, "_devices", [])
        for device in devices:
            if device["name"] == choice:
                self.device_index = device["index"]
                return
        self.device_index = None

    # ------------------------------------------------------------------ #
    def _sync_project_state(self) -> None:
        project = self.app.project
        if project is None:
            self.transcribe_button.configure(state="disabled")
            return
        audio = self.app.library.audio_path(project.id)
        self.transcribe_button.configure(state="normal" if audio.exists() else "disabled")

    def _toggle_recording(self) -> None:
        if self.recorder is not None and self.recorder.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        if not self.app.require_project():
            return
        if not sounddevice_available():
            self.app.set_status("Install 'sounddevice' to record, or import an audio file.")
            self._import_audio()
            return

        self.recorder = AudioRecorder(device=self.device_index)
        try:
            self.recorder.start()
        except Exception as exc:
            self.recorder = None
            self.app.set_status(str(exc))
            return

        self.record_button.configure(text="Stop recording", fg_color=COLORS["warning"], hover_color="#b3801b")
        self.app.set_status("Recording...")
        self._start_meters()

    def _stop_recording(self) -> None:
        if self.recorder is None:
            return
        project = self.app.project
        path = self.app.library.audio_path(project.id)
        try:
            written = self.recorder.stop(path)
        except Exception as exc:
            self.app.set_status(f"Could not save the recording: {exc}")
            written = None
        finally:
            self.recorder = None
            self._stop_meters()

        self.record_button.configure(text="Start recording", fg_color=COLORS["danger"], hover_color="#d43f38")
        self.level_bar.set(0)

        if written and written.exists():
            project.status = ProjectStatus.RECORDED
            project.audio_filename = written.name
            self.app.library.save(project)
            self.transcribe_button.configure(state="normal")
            self.hint_label.configure(text="Recording saved. Transcribe when you are ready.")
            self.app.set_status(f"Recording saved ({written.stat().st_size // 1024} KB).")

    def _import_audio(self) -> None:
        if not self.app.require_project():
            return
        chosen = filedialog.askopenfilename(title="Choose an audio file", filetypes=AUDIO_FILETYPES)
        if not chosen:
            return
        source = Path(chosen)
        target = self.app.library.audio_path(self.app.project.id)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_bytes(source.read_bytes())
        except OSError as exc:
            self.app.set_status(f"Could not import the file: {exc}")
            return
        self.app.project.status = ProjectStatus.RECORDED
        self.app.project.audio_filename = target.name
        self.app.library.save(self.app.project)
        self.transcribe_button.configure(state="normal")
        self.hint_label.configure(text=f"Imported {source.name}")
        self.app.set_status(f"Imported {source.name}.")

    def _manual_entry(self) -> None:
        if not self.app.require_project():
            return
        self.app.navigate("TranscriptPage", manual=True)

    # ------------------------------------------------------------------ #
    def _start_meters(self) -> None:
        self._tick()
        self._tick_meter()

    def _stop_meters(self) -> None:
        for job_name in ("_ticker_job", "_meter_job"):
            job = getattr(self, job_name, None)
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, job_name, None)

    def _tick(self) -> None:
        if self.recorder is None or not self.recorder.recording:
            return
        total = int(self.recorder.duration)
        self.timer_label.configure(text=f"{total // 60:02d}:{total % 60:02d}")
        self._ticker_job = self.after(500, self._tick)

    def _tick_meter(self) -> None:
        if self.recorder is None or not self.recorder.recording:
            return
        level = max(0.0, min(1.0, self.recorder.level))
        self.level_bar.set(level)
        self.level_text.configure(text=f"{int(level * 100)}%" if level > 0.01 else "")
        self._meter_job = self.after(60, self._tick_meter)

    # ------------------------------------------------------------------ #
    def _transcribe(self) -> None:
        if not self.app.require_project():
            return
        project = self.app.project
        pipeline = self.app.pipeline

        self.transcribe_button.configure(state="disabled", text="Transcribing...")
        self.progress.grid()
        self.progress_label.grid()
        self.progress.set(0.05)
        self.progress_label.configure(text="Transcribing audio...")

        def work(report):
            pipeline.transcribe(project, report)
            pipeline.split_chapters(project, report)
            return project

        def on_done(result):
            self.progress.set(1.0)
            self.progress_label.configure(text="Transcript ready.")
            self.transcribe_button.configure(state="normal", text="Transcribe again")
            self.app.navigate("TranscriptPage")

        def on_error(error):
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.transcribe_button.configure(state="normal", text="Transcribe & continue")
            hint = getattr(error, "hint", "")
            self.app.set_status(str(error))
            self._show_error(error, hint)

        self.app.run_background(work, on_done=on_done, on_error=on_error, status="Transcribing...")

    def _show_error(self, error: Exception, hint: str) -> None:
        from tkinter import messagebox

        text = str(error)
        if hint:
            text = f"{text}\n\n{hint}"
        messagebox.showerror("Transcription failed", text)
