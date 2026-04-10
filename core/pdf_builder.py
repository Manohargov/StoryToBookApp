from fpdf import FPDF
import os
from config import OUTPUT_DIR

class BookPDF(FPDF):
    def __init__(self, book_data):
        super().__init__()
        self.book_data = book_data
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def _add_cover(self):
        self.add_page()
        cover_path = self.book_data.get("cover_image")
        if cover_path and os.path.exists(cover_path):
            self.image(cover_path, x=10, y=10, w=190)
        else:
            self.ln(80)
            self.set_font("Arial", "B", 28)
            self.cell(0, 20, self.book_data["title"], 0, 1, "C")
            self.ln(10)
            self.set_font("Arial", "", 18)
            self.cell(0, 15, f"by {self.book_data['author']}", 0, 1, "C")

    def _add_title_page(self):
        self.add_page()
        self.ln(60)
        self.set_font("Arial", "B", 26)
        self.cell(0, 20, self.book_data["title"], 0, 1, "C")
        self.ln(15)
        self.set_font("Arial", "", 18)
        self.cell(0, 15, f"by {self.book_data['author']}", 0, 1, "C")
        if self.book_data.get("publisher"):
            self.ln(60)
            self.set_font("Arial", "I", 14)
            self.cell(0, 10, self.book_data["publisher"], 0, 1, "C")

    def _add_ack_and_note(self):
        self.add_page()
        self.set_font("Arial", "B", 18)
        self.cell(0, 15, "Acknowledgment", 0, 1, "L")
        self.ln(5)
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 8, self.book_data.get("acknowledgment", "Thank you for reading."))
        self.ln(15)
        self.set_font("Arial", "B", 18)
        self.cell(0, 15, "Author's Note", 0, 1, "L")
        self.ln(5)
        self.multi_cell(0, 8, self.book_data.get("author_note", "Created with StoryToBook AI."))

    def _add_toc(self):
        self.add_page()
        self.set_font("Arial", "B", 20)
        self.cell(0, 15, "Table of Contents", 0, 1, "C")
        self.ln(10)
        self.set_font("Arial", "", 12)
        for i in range(len(self.book_data.get("chapters", []))):
            self.cell(0, 10, f"Chapter {i+1}", 0, 1, "L")

    def _add_chapters(self):
        for i, chapter in enumerate(self.book_data.get("chapters", []), 1):
            self.add_page()
            self.set_font("Arial", "B", 20)
            self.cell(0, 15, f"Chapter {i}", 0, 1, "C")
            self.ln(5)
            self.set_font("Arial", "", 12)
            self.multi_cell(0, 8, chapter)

    def _add_last_page(self):
        self.add_page()
        self.ln(100)
        self.set_font("Arial", "I", 14)
        self.cell(0, 10, "Thank you for reading!", 0, 1, "C")
        self.ln(20)
        self.set_font("Arial", "", 12)
        self.cell(0, 10, f"Written by {self.book_data['author']}", 0, 1, "C")
        if self.book_data.get("publisher"):
            self.ln(10)
            self.cell(0, 10, f"Published by {self.book_data['publisher']}", 0, 1, "C")
        self.ln(20)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "© All rights reserved", 0, 1, "C")

    def generate(self, output_filename="book.pdf"):
        print("[PDF] Compiling book...")
        self._add_cover()
        self._add_title_page()
        self._add_ack_and_note()
        self._add_toc()
        self._add_chapters()
        self._add_last_page()

        output_path = OUTPUT_DIR / output_filename
        self.output(str(output_path))
        print(f"[PDF] Saved to {output_path}")
        return str(output_path)