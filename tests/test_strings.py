import pytest

from utils.strings import to_snake_case


def test_to_snake_case_strips_accents_and_lowercases():
    assert to_snake_case("Mérida") == "merida"


def test_to_snake_case_collapses_and_trims_underscores():
    assert to_snake_case("  San Cristóbal - Centro  ") == "san_cristobal_centro"


def test_to_snake_case_keeps_alnum_and_underscore():
    assert to_snake_case("Apto_12B") == "apto_12b"


def test_to_snake_case_punctuation_becomes_single_underscores():
    assert to_snake_case("Hello, world!") == "hello_world"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Caracas", "caracas"),
        ("Los Teques / Miranda", "los_teques_miranda"),
        ("--Foo---Bar--", "foo_bar"),
    ],
)
def test_to_snake_case_examples(raw, expected):
    assert to_snake_case(raw) == expected
