import pytest
from helper_testsuite import wrapper_test_good

from backend.read_pdf.read_pdf import read_all_pdf
from vars import PATH_TEST_DOCS_TESTSUITE

TEXT_NATIVE = "Communauté d’Agglomération des Portes du Hainaut – Construction d’un Centre Aquatique à St Amand Les Eaux – CR MOE N° 01 du   15/03/11 \n Page 2 sur 7 \n \nLOTS N° : \nENTREPRISES \nReprésentant \nTéléphone \nPortable \nFax \nEmail \nP\nC\n \nLot 1 \nSONDEFOR \nM. PETIT \n05.49.56.59.49 \n06 12 42 75 03 \n"
TEXT_SCANNED = "COUR D’APPEL DE ROUEN\n\n| DES MINUTES DU GREFFE\nDU TRIBUNAL JUDICIAIRE DE ROUEN\nil a été extrait ce qui suit :\n\nTRIBUNAL JUDICIAIRE DE ROUEN\n\nPAC - Référés\n\nN° RG 24/00954 - N° Portalis"


@pytest.mark.parametrize(
    ["filename", "expected_text"],
    [("native", TEXT_NATIVE), ("scanned", TEXT_SCANNED)],
)
def test_read_pdf(filename: str, expected_text: str) -> None:
    path = PATH_TEST_DOCS_TESTSUITE / "read_pdf" / f"{filename}.pdf"

    def f():
        texts = read_all_pdf(pdf_path=path)
        assert texts[0].startswith(expected_text)

    wrapper_test_good(runnable=f)
