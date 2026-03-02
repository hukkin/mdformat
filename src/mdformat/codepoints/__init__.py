__all__ = (
    "UNICODE_PUNCTUATION",
    "UNICODE_WHITESPACE",
    "ASCII_CTRL",
)


from mdformat.codepoints._unicode_punctuation import UNICODE_PUNCTUATION
from mdformat.codepoints._unicode_whitespace import UNICODE_WHITESPACE

ASCII_CTRL = frozenset(chr(i) for i in range(32)) | frozenset(chr(127))
