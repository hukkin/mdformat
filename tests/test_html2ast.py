from mdformat._util import HTML2AST


def test_html2ast():
    data = HTML2AST().parse('<div><p class="x">a<s>j</s></p></div><a>b</a>')
    assert data == [
        {
            "tag": "div",
            "attrs": {},
            "children": [
                {
                    "tag": "p",
                    "attrs": {"class": "x"},
                    "data": ["a"],
                    "children": [{"tag": "s", "attrs": {}, "data": ["j"]}],
                }
            ],
        },
        {"tag": "a", "attrs": {}, "data": ["b"]},
    ]


def test_html2ast_multiline():
    data = HTML2AST().parse("<div>a\nb \nc \n\n</div>")
    assert data == [{"tag": "div", "attrs": {}, "data": ["a\nb \nc \n\n"]}]


def test_html2ast_nested():
    data = HTML2AST().parse("<a d=1>b<a d=2>c<a d=3>e</a></a></a>")
    assert data == [
        {
            "tag": "a",
            "attrs": {"d": "1"},
            "data": ["b"],
            "children": [
                {
                    "tag": "a",
                    "attrs": {"d": "2"},
                    "data": ["c"],
                    "children": [{"tag": "a", "attrs": {"d": "3"}, "data": ["e"]}],
                }
            ],
        }
    ]


def test_html2ast_strip():
    data = HTML2AST().parse('<div><p class="x y">a<s>j</s></p></div><a>b</a>', {"x"})
    assert data == [
        {
            "tag": "div",
            "attrs": {},
            "children": [{"tag": "p", "attrs": {"class": "x y"}}],
        },
        {"tag": "a", "attrs": {}, "data": ["b"]},
    ]


def test_html2ast_multiple_content():
    data = HTML2AST().parse(
        """
<div>
hello

<p class="x y">a</p>
<p class="a b"></p>

   another  hello  in  the same div
this one is multiline
</div>
""",
    )
    assert data == [
        {
            "tag": "div",
            "attrs": {},
            "children": [
                {"tag": "p", "attrs": {"class": "x y"}, "data": ["a"]},
                {"tag": "p", "attrs": {"class": "a b"}},
            ],
            "data": [
                "\nhello\n\n",
                "\n",
                """

   another  hello  in  the same div
this one is multiline
""",
            ],
        },
    ]


def test_html2ast_empty_paragraphs():
    data = HTML2AST().parse(
        """
<p></p>
<p>a</p>
<p>
</p>
<p> </p>
""",
    )
    assert data == [
        {"tag": "p", "attrs": {}},
        {"tag": "p", "attrs": {}, "data": ["a"]},
        {"tag": "p", "attrs": {}, "data": [""]},
        {"tag": "p", "attrs": {}, "data": [""]},
    ]
