import logging
from pathlib import Path
import PyPDF2


class Logger:
    """Simple logger wrapper"""

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)


class FileHandler:
    """Handles file reading for various formats"""

    @staticmethod
    def read_file(filepath):
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if path.suffix.lower() == '.pdf':
            return FileHandler._read_pdf(path)
        else:
            return FileHandler._read_text(path)

    @staticmethod
    def _read_pdf(path):
        text = ""
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
        return text.strip()

    @staticmethod
    def _read_text(path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
