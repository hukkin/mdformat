import pytest

from mdformat.renderer import _util


@pytest.mark.parametrize(
    "in_, indexes, out",
    [
        ("text", [0], ["", "text"]),
        ("text", [3], ["tex", "t"]),
        ("text", [4], ["text", ""]),
        (
            "lorem dipsum iksum lopsum",
            [0, 1, 6, 7],
            ["", "l", "orem ", "d", "ipsum iksum lopsum"],
        ),
    ],
)
def test_split_at_indexes(in_, indexes, out):
    assert _util.split_at_indexes(in_, indexes) == out


def test_split_at_indexes__valueerror():
    with pytest.raises(ValueError) as exc_info:
        _util.split_at_indexes("testtext", ())
    assert "indexes must not be empty" in str(exc_info.value)
