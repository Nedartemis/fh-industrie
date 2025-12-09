from abc import ABC, abstractmethod

import pytesseract
from PIL import Image

# from doctr.io import DocumentFile
# from doctr.models import ocr_predictor


class OCR(ABC):
    @abstractmethod
    def image_to_string(self, image) -> str:
        pass


class PytesseractOCR(OCR):

    def __init__(self, language: str):
        self._language = language

    def image_to_string(self, image: Image) -> str:
        return pytesseract.image_to_string(image, lang=self._language)


# class DoctrOCR(OCR):
# def __init__(self):
#     self._model = ocr_predictor(pretrained=True)

# def image_to_string(self, image: Image):
#     path_image = PATH_TMP / "image_to_ocr.png"
#     image.save(path_image)
#     doc = DocumentFile.from_images(path_image)
#     result = self._model(doc)
#     return result.render()
