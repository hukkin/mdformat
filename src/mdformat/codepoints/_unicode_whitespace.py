"""Pre-generated unicode whitespace characters.

Run this module to generate and print an up-to-date set of characters.
"""

UNICODE_WHITESPACE = frozenset(
    (
        "\t",
        "\n",
        "\x0c",
        "\r",
        " ",
        "\xa0",
        "\u1680",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200a",
        "\u202f",
        "\u205f",
        "\u3000",
    )
)

if __name__ == "__main__":
    import sys
    import unicodedata

    UNICODE_CHARS = frozenset(chr(c) for c in range(sys.maxunicode + 1))
    UNICODE_WHITESPACE = frozenset(
        c for c in UNICODE_CHARS if unicodedata.category(c) == "Zs"
    ) | frozenset("\t\n\f\r")
    print(f"frozenset({tuple(sorted(UNICODE_WHITESPACE))})")
