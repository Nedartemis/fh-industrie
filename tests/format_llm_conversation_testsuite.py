from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pytest
from helper_testsuite import bed, bied, biv, wrapper_test_good, wrapper_test_logs

from backend.extraction.format_llm_conversation import (
    build_prompt_exact_infos,
    build_prompt_short_and_list_infos,
    find_index,
    from_response_llm_exact_info_extract_exact_text,
    postprocess_llm_answer_short_list_info,
)
from backend.info_struct import ExtractionData, InfoExtractionDatas, InfoValues
from logs_label import LlmWrongFormat

# ------------------- Utils -------------------


def simpliy_prompt(s: str):
    return s.strip().replace("\t", "").replace(" ", "")


# ------------------- Prompt short and list -------------------


@pytest.mark.parametrize(
    ["infos", "expected_str"],
    [
        (bied(inds=bed(name="n1")), '"n1" : "string"'),
        (
            bied(inds=bed(name="n1", description="the description")),
            '"n1" : "string" # description : the description',
        ),
        (bied(lists={"n1": [bed(name="s1")]}), '"n1" : [{"s1" : "string"}, ...]'),
        (
            bied(lists={"n1": [bed(name="s1")], "n2": [bed(name="s1")]}),
            '"n1" : [{"s1" : "string"}, ...],\n' + '"n2" : [{"s1" : "string"}, ...]',
        ),
        (
            bied(lists={"n1": [bed(name="s1"), bed(name="s2")]}),
            '"n1" : [{"s1" : "string", "s2" : "string"}, ...]',
        ),
        (
            bied(
                inds=[bed(name="n1"), bed(name="n2", description="the description")],
                lists={"n3": [bed(name="s1"), bed(name="s2")]},
            ),
            '"n1" : "string",\n'
            + '"n2" : "string" # description : the description,\n'
            + '"n3" : [{"s1" : "string", "s2" : "string"}, ...]',
        ),
    ],
)
def test_prompt_short_list(infos: InfoExtractionDatas, expected_str: str):

    def f():
        actual = build_prompt_short_and_list_infos(infos)

        expected = f"""Extrait toutes les informations que tu trouves sous format json :
        ```json
        {'{'}
            {expected_str}
        {'}'}```

        Si tu ne trouves pas l'info, remplie le champs par "None".
        """

        assert actual

        assert simpliy_prompt(actual) == simpliy_prompt(expected)

    wrapper_test_good(runnable=f)


# ------------------- Prompt exact -------------------


@pytest.mark.parametrize(
    ["ed"],
    [
        (bed(name="n1", exact=True),),
        (
            bed(
                name="n1",
                description="the description",
                exact=True,
            ),
        ),
    ],
)
def test_prompt_exact(ed: ExtractionData):

    def f():
        actual = build_prompt_exact_infos(ed=ed)

        expected = f"""
        Extraire le début et la fin de cette information '{ed.name}'{"ayant cette description : " + ed.description if ed.description else ''}."

        Le format doit être le suivant :
        ```json
        {'{'}
            "debut" : "string",
            "fin" : "string"
        {'}'}```
        """

        assert actual
        assert simpliy_prompt(actual) == simpliy_prompt(expected)

    wrapper_test_good(runnable=f)


# ------------------- Post process short and list -------------------


@pytest.mark.parametrize(
    ["extracted_json", "info_values_expected"],
    [
        # inds
        ({"n1": "v1"}, biv(inds={"n1": "v1"})),
        ({"n1": "v1", "n2": "v2"}, biv(inds={"n1": "v1", "n2": "v2"})),
        # lists
        ({"n1": [{"s1": "v1"}]}, biv(lists={"n1": [{"s1": "v1"}]})),
        (
            {"n1": [{"s1": "v1", "s2": "v2"}]},
            biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]}),
        ),
        (
            {"n1": [{"s1": "v1"}], "n2": [{"s1": "v1"}]},
            biv(lists={"n1": [{"s1": "v1"}], "n2": [{"s1": "v1"}]}),
        ),
        # both
        (
            {"n1": "v1", "n2": [{"s1": "v2"}]},
            biv(inds={"n1": "v1"}, lists={"n2": [{"s1": "v2"}]}),
        ),
        # None
        ({"n1": "None"}, biv(inds={"n1": None})),
        ({"n1": "none"}, biv(inds={"n1": None})),
        ({"n1": [{"s1": "None"}]}, biv(lists={"n1": [{"s1": None}]})),
    ],
)
def test_postprocess_short_and_list_good(
    extracted_json: Dict[str, Union[str, List[Dict[str, str]]]],
    info_values_expected: InfoValues,
):
    def f():
        actual = postprocess_llm_answer_short_list_info(extracted_json=extracted_json)
        assert actual == info_values_expected

    wrapper_test_good(runnable=f)


@pytest.mark.parametrize(
    ["extracted_json", "expected_log_label_class", "exected_info_values"],
    [
        # root type
        ([], LlmWrongFormat, biv()),
        ({"n1", "v1"}, LlmWrongFormat, biv()),
        ({1: "v1"}, LlmWrongFormat, biv()),
        ({"n1": 1}, LlmWrongFormat, biv()),
        ({"n1": 1, "n2": "v2"}, LlmWrongFormat, biv(inds={"n2": "v2"})),
        # lists
        ({"n1": ["toto"]}, LlmWrongFormat, biv()),
        ({"n1": [1]}, LlmWrongFormat, biv()),
        ({"n1": [{1}]}, LlmWrongFormat, biv()),
        ({"n1": [{"s1": "v1"}, 1]}, LlmWrongFormat, biv()),
        ({"n1": [{"s1": 1}]}, LlmWrongFormat, biv()),
        ({"n1": [{1: "v1"}]}, LlmWrongFormat, biv()),
        (
            {"n1": [1], "n2": [{"s1": "v1"}]},
            LlmWrongFormat,
            biv(lists={"n2": [{"s1": "v1"}]}),
        ),
        # many errors
        (
            {
                # good ones
                "n1": "v1",
                "n2": [{"s1": "v1"}],
                # root not good
                1: "v2",  # +1 LlmWrongFormat
                "n4": 1,  # +1 LlmWrongFormat
                # lists
                "n5": [1],  # n5-8 : +1 LlmWrongFormat
                "n6": [{1}],
                "n7": [{"n1": 1}],
                "n8": [{1: "v2"}],
            },
            [LlmWrongFormat] * 3,
            biv(inds={"n1": "v1"}, lists={"n2": [{"s1": "v1"}]}),
        ),
    ],
)
def test_postprocess_short_and_list_wrong(
    extracted_json: Any, expected_log_label_class, exected_info_values: InfoValues
):

    def f():
        info_values = postprocess_llm_answer_short_list_info(
            extracted_json=extracted_json
        )
        assert info_values == exected_info_values

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


@pytest.mark.parametrize(
    ["text_where_to_search", "extracted_json", "expected_str"],
    [
        ("1", {"debut": "1", "fin": "1"}, "1"),
        ("123", {"debut": "1", "fin": "3"}, "123"),
        ("je vois la vie en rose", {"debut": "vois", "fin": "en"}, "vois la vie en"),
        (
            "je vois la vie en rose",
            {"debut": "vois la", "fin": "vie en"},
            "vois la vie en",
        ),
    ],
)

# ------------------- Post process exact -------------------


def test_post_process_exact_good(
    text_where_to_search: str, extracted_json: dict, expected_str: str
):
    def f():
        actual_str = from_response_llm_exact_info_extract_exact_text(
            text_where_to_search, extracted_json
        )
        assert actual_str == expected_str

    wrapper_test_good(runnable=f)


@pytest.mark.parametrize(
    ["text_where_to_search", "extracted_json", "expected_log_label_class"],
    [
        ("", 1, LlmWrongFormat),
        ("", {}, LlmWrongFormat),
        ("1", {"debut": 1, "fin": "1"}, LlmWrongFormat),
        ("1", {"debut": "1", "fin": 1}, LlmWrongFormat),
        ("1", {"debut": "1"}, LlmWrongFormat),
        ("1", {"debut": "1"}, LlmWrongFormat),
        ("1", {"fin": "1"}, LlmWrongFormat),
        ("1", {"debut": "1", "fin": "2"}, LlmWrongFormat),
        ("1", {"debut": "2", "fin": "1"}, LlmWrongFormat),
    ],
)
def test_postprocess_exact_wrong(
    text_where_to_search: str, extracted_json: dict, expected_log_label_class: str
):

    def f():
        info_values = from_response_llm_exact_info_extract_exact_text(
            text_where_to_search=text_where_to_search, extracted_json=extracted_json
        )
        assert info_values == None

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


# ------------------- find index -------------------


@pytest.mark.parametrize(
    ["text", "pattern", "expected_found_text"],
    [
        (
            """Avant-dire droit sur la demande tendant à voir ordonner la mise en œuvre de la
garantie de parfait achèvement, ,

ORDONNE une mission d'expertise confiée à

M. Franck Hibon

6, impasse des Hautes Terres

76550 Saint-Aubin-sur-Scie

expert inscrit sur la liste de la cour d’appel de Rouen,

DIT que l'expert aura pour mission de :

Après avoir pris connaissance de tous documents contractuels et techniques, tels que
l’acte de vente, plans, devis, marchés et autres et s’être rendu sur les lieux situés à
Caumont, 32, rue des 3 épines, après y avoir préalablement convoqué les parties et

leurs avocats respectifs ;

I. Environnement

1 Situer et décrire l'immeuble avant les travaux, préciser qui en était le propriétaire,
le ou les occupants, décrire son utilisation.

2. Décrire les travaux, tant d’un point de vue matériel que juridique, en identifiant
chaque partie intervenue, son rôle et leurs relations contractuelles.""",
            "Après avoir pris connaissance de tous documents contractuels et techniques, tels que l'acte de vente, plans, devis, marchés et autres et s'être rendu sur les lieux situés à Caumont, 32, rue des 3 épines, après y avoir préalablement convoqué les parties et leurs avocats respectifs ;",
            """Après avoir pris connaissance de tous documents contractuels et techniques, tels que
l’acte de vente, plans, devis, marchés et autres et s’être rendu sur les lieux situés à
Caumont, 32, rue des 3 épines, après y avoir préalablement convoqué les parties et

leurs avocats respectifs """,
        ),
    ],
)
def test_find_index(text: str, pattern: str, expected_found_text: str):
    idx = find_index(text=text, pattern=pattern)
    assert idx

    actual = text[idx : idx + len(pattern)]
    assert actual == expected_found_text
