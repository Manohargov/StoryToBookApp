import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import platform
import subprocess
from pathlib import Path

from config import BASE_DIR, OUTPUT_DIR, TEMP_DIR
from core.audio_recorder import AudioRecorder
from core.transcriber import Transcriber
from core.text_processor import TextProcessor
from core.cover_generator import CoverGenerator
from core.pdf_builder import BookPDF

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Story to Book")
        self.geometry("850x650")
        self.resizable(False, False)

        self.book_data = {
            "title": "", "author": "", "publisher": "",
            "acknowledgment": "", "author_note": "",
            "chapters": [], "full_text": "", "cover_image": ""
        }

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.frames = {}
        for F in (LandingPage, DashboardPage, RecordingPage, ProcessingPage, BookDetailsPage, ExportPage):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LandingPage")

    def show_frame(self, name):
        self.frames[name].tkraise()

    def reset_book_data(self):
        self.book_data = {k: ("" if k != "chapters" else []) for k in self.book_data}

class LandingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ctk.CTkLabel(self, text="📖 Story to Book", font=("Arial", 36, "bold")).pack(pady=60)
        ctk.CTkLabel(self, text="Transform your voice into a published book", font=("Arial", 16), text_color="gray").pack(pady=5)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=40)
        ctk.CTkButton(btn_frame, text="Sign In", width=200, command=lambda: controller.show_frame("DashboardPage")).pack(pady=10)
        ctk.CTkButton(btn_frame, text="Create Account", width=200, command=lambda: controller.show_frame("DashboardPage")).pack(pady=10)

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ctk.CTkLabel(self, text="📂 Project Dashboard", font=("Arial", 24, "bold")).pack(pady=20)
        ctk.CTkButton(self, text="✨ Start New Recording", width=300, height=50, 
                      command=lambda: controller.show_frame("RecordingPage")).pack(pady=30)
        ctk.CTkLabel(self, text="Previous projects will appear here.", text_color="gray").pack(pady=10)

class RecordingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.recorder = AudioRecorder(str(TEMP_DIR / "recording.wav"))
        
        ctk.CTkLabel(self, text="🎙️ Audio Recording", font=("Arial", 24, "bold")).pack(pady=20)
        self.status_lbl = ctk.CTkLabel(self, text="Press Start to record", font=("Arial", 14))
        self.status_lbl.pack(pady=10)
        
        self.btn_record = ctk.CTkButton(self, text="⏺ Start Recording", fg_color="red", width=200, command=self.toggle_recording)
        self.btn_record.pack(pady=20)
        
        self.btn_next = ctk.CTkButton(self, text="Finish & Process", state="disabled", width=200, command=self.finish)
        self.btn_next.pack(pady=10)

    def toggle_recording(self):
        if not self.recorder.recording:
            self.recorder.start()
            self.btn_record.configure(text="⏹ Stop Recording")
            self.status_lbl.configure(text="Recording... Speak clearly")
        else:
            self.recorder.stop()
            self.btn_record.configure(text="⏺ Start Recording")
            self.status_lbl.configure(text="Recording saved")
            self.btn_next.configure(state="normal")

    def finish(self):
        self.controller.show_frame("ProcessingPage")

class ProcessingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ctk.CTkLabel(self, text="⚙️ Processing Audio", font=("Arial", 24, "bold")).pack(pady=40)
        self.status_lbl = ctk.CTkLabel(self, text="Initializing...", font=("Arial", 14))
        self.status_lbl.pack(pady=10)
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=20)
        self.progress.start()
        
        threading.Thread(target=self.run_processing, daemon=True).start()

    def run_processing(self):
        try:
            self.status_lbl.configure(text="Transcribing audio...")
            self.progress.set(0.2)
            
            transcriber = Transcriber()
            text = transcriber.transcribe(str(TEMP_DIR / "recording.wav"))
            self.controller.book_data["full_text"] = text
            
            self.status_lbl.configure(text="Splitting into chapters...")
            self.progress.set(0.6)
            
            processor = TextProcessor()
            self.controller.book_data["chapters"] = processor.split_into_chapters(text)
            
            self.progress.set(1.0)
            self.status_lbl.configure(text="Processing complete!")
            self.after(500, lambda: self.controller.show_frame("BookDetailsPage"))
        except Exception as e:
            self.status_lbl.configure(text=f"Error: {e}")
            self.progress.stop()

class BookDetailsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ctk.CTkLabel(self, text="📝 Book Details", font=("Arial", 24, "bold")).pack(pady=15)
        
        fields = [
            ("Book Title", "entry_title", "Enter book title"),
            ("Author Name", "entry_author", "Enter author name"),
            ("Publisher (Optional)", "entry_publisher", "Enter publisher"),
        ]
        
        self.entries = {}
        for label, attr, placeholder in fields:
            ctk.CTkLabel(self, text=label).pack(pady=(10,0))
            entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=400)
            entry.pack(pady=5)
            self.entries[attr] = entry

        ctk.CTkLabel(self, text="Acknowledgment (Optional)").pack(pady=(10,0))
        self.txt_ack = ctk.CTkTextbox(self, width=400, height=60)
        self.txt_ack.pack(pady=5)

        ctk.CTkLabel(self, text="Author Note (Optional)").pack(pady=(10,0))
        self.txt_note = ctk.CTkTextbox(self, width=400, height=60)
        self.txt_note.pack(pady=5)

        ctk.CTkLabel(self, text="Fine-tuned Model Path (Optional)").pack(pady=(10,0))
        self.entry_model = ctk.CTkEntry(self, placeholder_text="Default: fine_tuned_model", width=400)
        self.entry_model.pack(pady=5)

        self.gen_btn = ctk.CTkButton(self, text="🚀 Generate Cover & Create Book", width=400, command=self.start_generation)
        self.gen_btn.pack(pady=20)
        
        self.status_lbl = ctk.CTkLabel(self, text="", font=("Arial", 12), text_color="yellow")
        self.status_lbl.pack(pady=5)

    def start_generation(self):
        title = self.entries["entry_title"].get().strip()
        author = self.entries["entry_author"].get().strip()
        if not title or not author:
            messagebox.showerror("Missing Info", "Title and Author are required.")
            return

        self.controller.book_data.update({
            "title": title, "author": author,
            "publisher": self.entries["entry_publisher"].get().strip(),
            "acknowledgment": self.txt_ack.get("1.0", "end-1c").strip(),
            "author_note": self.txt_note.get("1.0", "end-1c").strip()
        })

        self.gen_btn.configure(state="disabled", text="Generating...")
        model_path = self.entry_model.get().strip() or None
        threading.Thread(target=self.run_generation, args=(model_path,), daemon=True).start()

    def run_generation(self, model_path):
        try:
            self.safe_update("Loading AI model...")
            gen = CoverGenerator(model_path)
            gen.load_model()
            
            self.safe_update("Generating cover from story theme...")
            cover_path = gen.generate(
                self.controller.book_data["full_text"],
                self.controller.book_data["title"],
                self.controller.book_data["author"]
            )
            self.controller.book_data["cover_image"] = cover_path
            
            self.safe_update("Compiling PDF book...")
            filename = f"{self.controller.book_data['title'].replace(' ', '_')}.pdf"
            pdf = BookPDF(self.controller.book_data)
            pdf.generate(filename)
            
            self.safe_update("✅ Complete!")
            self.after(500, lambda: self.controller.show_frame("ExportPage"))
        except Exception as e:
            self.safe_update(f"❌ Error: {e}")
            self.after(0, lambda: self.gen_btn.configure(state="normal", text="🚀 Generate Cover & Create Book"))

    def safe_update(self, text):
        self.after(0, lambda: self.status_lbl.configure(text=text))

class ExportPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ctk.CTkLabel(self, text="🎉 Book Ready!", font=("Arial", 36, "bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Your PDF has been successfully created.", font=("Arial", 16)).pack(pady=10)
        
        self.path_lbl = ctk.CTkLabel(self, text="", font=("Arial", 12), text_color="gray")
        self.path_lbl.pack(pady=15)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="📁 Open Folder", command=self.open_folder, width=180).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔄 Create Another", command=self.reset, width=180).pack(side="left", padx=10)

    def reset(self):
        self.controller.reset_book_data()
        self.controller.show_frame("DashboardPage")

    def open_folder(self):
        path = str(OUTPUT_DIR)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

if __name__ == "__main__":
    app = StoryApp()
    app.mainloop()