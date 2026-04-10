from config import PROCESSING_CONFIG

class TextProcessor:
    def __init__(self):
        self.chapter_length = PROCESSING_CONFIG["chapter_word_count"]

    def split_into_chapters(self, full_text):
        words = full_text.split()
        chapters = []
        current_chapter = []

        for word in words:
            current_chapter.append(word)
            if len(current_chapter) >= self.chapter_length:
                # Try to split at sentence boundary
                chunk = " ".join(current_chapter)
                last_period = chunk.rfind(".")
                if last_period != -1 and last_period > len(chunk) * 0.5:
                    chapters.append(chunk[:last_period+1].strip())
                    remaining = chunk[last_period+1:].strip()
                    current_chapter = remaining.split() if remaining else []
                else:
                    chapters.append(chunk.strip())
                    current_chapter = []

        if current_chapter:
            chapters.append(" ".join(current_chapter).strip())

        return chapters