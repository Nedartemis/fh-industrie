import tempfile
from pathlib import Path
from typing import List, Optional

# import fitz  # PyMuPDF
import pymupdf
from pdf2image import convert_from_path
from tqdm import tqdm

from backend.read_pdf.ocr import PytesseractOCR
from logger import logger
from logs_label import ExtensionFileNotSupported, FileDataError, PathNotExisting

# ------------------- Public Method -------------------


def is_scanned(pdf_path: Path) -> bool:

    _check_ext(pdf_path)

    text = "".join(_read_pdf_natiely(pdf_path))
    return not text


def read_all_pdf(pdf_path: Path) -> List[str]:

    _check_ext(pdf_path)

    if is_scanned(pdf_path):
        return _ocr_pdf(pdf_path)
    else:
        return _read_pdf_natiely(pdf_path)


# ------------------- Private Method -------------------


def _check_ext(pdf_path: Path) -> None:
    if pdf_path.suffix != ".pdf":
        raise ExtensionFileNotSupported(path=pdf_path)


def _read_pdf_natiely(pdf_path: Path) -> List[str]:

    if not pdf_path.exists():
        raise PathNotExisting(path=pdf_path)

    try:
        with pymupdf.open(pdf_path) as doc:
            pages = [page.get_text() for page in doc]
    except pymupdf.FileDataError:
        raise FileDataError(path=pdf_path)

    return pages


# def _pdf_to_images(pdf_path, output_folder):
#     pdf_document = fitz.open(pdf_path)

#     paths = []
#     for page_num in range(len(pdf_document)):
#         page = pdf_document[page_num]
#         pix = page.get_pixmap()
#         output_path = f"{output_folder}/page_{page_num + 1}.png"
#         pix.save(output_path)
#         print(f"Saved {output_path}")
#         paths.append(output_path)
#     return paths


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

    if not pdf_path.exists():
        raise PathNotExisting(path=pdf_path)

    ocr = PytesseractOCR(language="fra")
    # ocr = DoctrOCR()

    # Create temp directory for storing images
    with tempfile.TemporaryDirectory() as temp_dir:

        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"PDF converted to {len(images)} images.")
        except Exception as e:
            raise FileDataError(path=pdf_path)

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
    from vars import PATH_TEST_DOCS

    path = (
        PATH_TEST_DOCS
        / "test_description"
        / "TJ ROUEN_24800954_LEBRETON_Ordonnance.pdf"
    )
    print(is_scanned(path))
    res = read_all_pdf(path)
    print(res[0])
