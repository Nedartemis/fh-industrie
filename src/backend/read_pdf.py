import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm


# TODO
def is_scanned(pdf_path: Path) -> bool:
    return True


def read_all_pdf(pdf_path: Path):

    if is_scanned(pdf_path):
        return ocr_pdf(pdf_path)
    else:
        raise NotImplementedError("Reading a native pdf is not implemented.")


def ocr_pdf(
    pdf_path: Path, pages: Optional[List[int]] = None, language="fra", dpi=300
) -> List[str]:
    """
    Performs OCR on a PDF and return the text.

    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path to save the output text. If None, uses the PDF name with .txt extension
        language (str, optional): Language for OCR. Default is 'eng'
        dpi (int, optional): DPI for rendering PDF. Higher is better quality but slower.
    """

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
            pages = list(range(len(images)))

        # Process each page
        text_per_page = []
        for i, image in tqdm(list(enumerate(images)), desc="OCR pages"):
            page_number = i + 1
            if not page_number in pages:
                continue

            # Perform OCR
            text = pytesseract.image_to_string(image, lang=language)
            text_per_page.append(text)

    return text_per_page
