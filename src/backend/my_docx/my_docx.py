from pathlib import Path

from docx import Document as OpenDocument
from docx.document import Document as DocumentObject


class Docx(DocumentObject):
    def __init__(self, path: Path):
        object.__setattr__(self, "_doc", OpenDocument(path))
        self.path = path

    def __getattr__(self, name):
        return getattr(self._doc, name)

    def __setattr__(self, name, value):
        setattr(self._doc, name, value)

    def __delattr__(self, name):
        delattr(self._doc, name)
