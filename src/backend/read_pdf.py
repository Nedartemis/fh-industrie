import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import pymupdf
import pytesseract
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from pdf2image import convert_from_path
from PIL import Image
from PIL.Image import Image
from tqdm import tqdm

from vars import PATH_TMP


class OCR(ABC):
    @abstractmethod
    def image_to_string(self, image) -> str:
        pass


class PytesseractOCR(OCR):

    def __init__(self, language: str):
        self._language = language

    def image_to_string(self, image: Image) -> str:
        return pytesseract.image_to_string(image, lang=self._language)


class DoctrOCR(OCR):
    def __init__(self):
        self._model = ocr_predictor(pretrained=True)

    def image_to_string(self, image: Image):
        path_image = PATH_TMP / "image_to_ocr.png"
        image.save(path_image)
        doc = DocumentFile.from_images(path_image)
        result = self._model(doc)
        return result.render()


# ------------------- Public Method -------------------


def is_scanned(pdf_path: Path) -> bool:

    text = "".join(_read_pdf_natiely(pdf_path))
    return not text


def read_all_pdf(pdf_path: Path) -> List[str]:

    if is_scanned(pdf_path):
        return _ocr_pdf(pdf_path)
    else:
        return _read_pdf_natiely(pdf_path)


# ------------------- Private Method -------------------


def _read_pdf_natiely(pdf_path: Path) -> List[str]:
    with pymupdf.open(pdf_path) as doc:
        pages = [page.get_text() for page in doc]
    return pages


def _ocr_pdf(
    pdf_path: Path,
    pages: Optional[List[int]] = None,
    dpi=300,
) -> List[str]:
    """
    Performs OCR on a PDF and return the text.

    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path to save the output text. If None, uses the PDF name with .txt extension
        language (str, optional): Language for OCR. Default is 'eng'
        dpi (int, optional): DPI for rendering PDF. Higher is better quality but slower.
    """
    ocr = PytesseractOCR(language="fra")
    # ocr = DoctrOCR()

    # Create temp directory for storing images
    with tempfile.TemporaryDirectory() as temp_dir:

        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
            print(f"PDF converted to {len(images)} images.")
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return None

        if pages is None:
            pages = list(range(1, len(images) + 1))

        # Process each page
        text_per_page = []
        for i, image in tqdm(list(enumerate(images)), desc="OCR pages"):

            page_number = i + 1
            if not page_number in pages:
                continue

            # Perform OCR
            text = ocr.image_to_string(image)

            # store result
            text_per_page.append(text)

    return text_per_page


# ------------------- Main -------------------

if __name__ == "__main__":
    from vars import PATH_TEST

    path = PATH_TEST / "test_description" / "TJ ROUEN_24800954_LEBRETON_Ordonnance.pdf"
    print(is_scanned(path))
    res = read_all_pdf(path)
    print(res[0])
