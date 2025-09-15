import json
from pathlib import Path

from _pytest.mark import ParameterSet
import pytest

import mdformat
from mdformat._util import is_md_equal

SPECTESTS_PATH = Path(__file__).parent / "data" / "commonmark_spec_v0.31.2.json"
SPECTESTS_CASES = tuple(
    {"name": str(entry["example"]), "md": entry["markdown"]}
    for entry in json.loads(SPECTESTS_PATH.read_text(encoding="utf-8"))
)
EXTRA_CASES = (
    {
        "name": "titles",
        "md": "# BIG Title\n"
        "## smaller\n"
        "### even smaller\n"
        "#### 4th level\n"
        "##### 5th level\n"
        "###### the smallest (6th level)\n",
    },
    {"name": "emphasis", "md": "*emphasized*\n" "**STRONGLY emphasized**\n"},
    {
        "name": "simple",
        "md": "# BIG Title\n" "> a quote here\n\n" "Paragraph is here.\n",
    },
    {"name": "strikethrough", "md": "# Testing strikethrough\n" "~~here goes~~\n"},
    {"name": "code span", "md": "`print('Hello World!)`\n"},
    {
        "name": "code span: double spaces",
        "md": "`  starts and ends with double spaces  `\n",
    },
    {"name": "escape char", "md": "\\*not emphasized\\*\n"},
    {
        "name": "fenced code",
        "md": "## Here's a code block\n"
        "```python\n"
        "print('Hello world!')\n"
        "```\n",
    },
    {"name": "paragraph line feeds", "md": "first paragraph\n\n" "second one\n"},
    {"name": "thematic break", "md": "thematic break\n\n" "---\n" "above\n"},
    {"name": "autolink", "md": "<http://foo.bar.baz>\n"},
    {"name": "link", "md": '[link](/uri "title")\n' "[link](/uri)\n" "[link]()\n"},
    {"name": "image", "md": '![foo](/url "title")\n' "![foo [bar](/url)](/url2)\n"},
    {"name": "unordered list", "md": "- item1\n" "- item2\n"},
    {"name": "unordered loose list", "md": "- item1\n" "\n" "- item2\n"},
    {"name": "ordered list", "md": "1. item1\n" "1. item2\n"},
    {"name": "ordered list 2", "md": "10021. item1\n" "10021. item2\n"},
    {"name": "ordered list zero", "md": "0. item1\n" "0. item2\n"},
    {"name": "whitespace preserve", "md": "- foo\n\n\tbar\n"},
    {"name": "debug", "md": "> ```\n> a\n> \n> \n> ```\n"},
    {"name": "list indentation", "md": "- foo\n\n\t\tbar\n"},
    {"name": "list in quote", "md": "> -"},
    {"name": "starts with >", "md": "\\>"},
    {"name": "reference link", "md": '[foo][bar]\n\n[bar]: /url "title"\n'},
    {"name": "empty file", "md": ""},
    {"name": "whitespace only", "md": "  \n\n \n  \n"},
    {"name": "starts with em space", "md": "&emsp;\n"},
    {"name": "starts with space", "md": "&#32;\n"},
    {"name": "trailing space", "md": "trailing space      &#32;\n"},
    {"name": "soft breaks", "md": "this is\nall one\nparagraph\n"},
    {"name": "escape underscore", "md": "# foo _bar_ \\_baz\\_\n"},
    {
        "name": "extend spectest 300",
        "md": "\\_not emphasized_\n"
        "1\\) not a list\n"
        "\\- not a list\n"
        "\\+ not a list\n",
    },
    {"name": "image link with brackets 1", "md": "![link](<foo(and(bar)>)\n"},
    {"name": "image link with brackets 2", "md": "![link](foo\\(and\\(bar\\))\n"},
    {"name": "image link with brackets 3", "md": "![link](foo\\)\\:)\n"},
    {"name": "image link with brackets 4", "md": "![a](<b)c>)\n"},
    {"name": "image link with brackets 5", "md": '![a](<b)c> "some title")\n'},
    {"name": "escaped thematic break (hyphen)", "md": "\\-\\-\\-\n"},
    {"name": "escaped thematic break (underscore v1)", "md": "\\_\\_\\_\n"},
    {"name": "escaped thematic break (underscore v2)", "md": "&#32;_ _ _&#32;\n"},
    {"name": "escaped thematic break (asterisk v1)", "md": "\\*\\*\\*\n"},
    {"name": "escaped thematic break (asterisk v2)", "md": "&#32;* * *&#32;\n"},
    {"name": "Hard break in setext heading", "md": "line1\\\nline2\n====\n"},
    {
        "name": "a mix of leading and trailing whitespace",
        "md": "&#9;foo\n"
        "&#32;&#32; foo &#9;&#32;\n"
        "&#9;foo \t\n"
        "  foo  \n"
        "\u2005foo\u2005\n"
        "foo\n",
    },
)
ALL_CASES = EXTRA_CASES + SPECTESTS_CASES


@pytest.mark.parametrize("wrap", ["keep", "no", 60])
@pytest.mark.parametrize("number", [True, False])
@pytest.mark.parametrize(
    "entry",
    ALL_CASES,
    ids=[
        (
            c.values[0]["name"]  # type: ignore[index]
            if isinstance(c, ParameterSet)
            else c["name"]
        )
        for c in ALL_CASES
    ],
)
def test_commonmark_spec(wrap, number, entry):
    """mdformat.text() against the Commonmark spec.

    Test that:
    1. Markdown AST is the same before and after 1 pass of formatting
    2. Markdown after 1st pass and 2nd pass of formatting are equal
    """
    options = {"wrap": wrap, "number": number}
    md_original = entry["md"]
    md_new = mdformat.text(md_original, options=options)
    md_2nd_pass = mdformat.text(md_new, options=options)
    assert is_md_equal(md_original, md_new, options=options)
    assert md_new == md_2nd_pass
