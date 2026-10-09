import pytest

import mdformat


@pytest.mark.parametrize(
    "source",
    [
        r"![a \* b](/u)",
        "![a &amp; b](/u)",
        r"![C:\Python26](/u)",
        r"![a \] b](/u)",
        "![a &#42; b](/u)",
        "![a &lt;tag&gt; b](/u)",
        r"![a \` b](/u)",
    ],
)
@pytest.mark.parametrize("wrap", ["keep", 20])
def test_image_alt_special_text(source, wrap):
    formatted = mdformat.text(source, options={"wrap": wrap})
    assert formatted == source + "\n"
    assert mdformat.text(formatted, options={"wrap": wrap}) == formatted
