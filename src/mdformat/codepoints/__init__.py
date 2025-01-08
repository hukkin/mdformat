__all__ = (
    "UNICODE_PUNCTUATION",
    "UNICODE_WHITESPACE",
    "ASCII_CTRL",
    "ASCII_WHITESPACE",
)


from mdformat.codepoints._unicode_punctuation import UNICODE_PUNCTUATION
from mdformat.codepoints._unicode_whitespace import UNICODE_WHITESPACE

ASCII_CTRL = frozenset(chr(i) for i in range(32)) | frozenset(chr(127))


def __getattr__(name: str) -> frozenset[str]:
    """Attribute getter fallback.

    Used during the deprecation period of `ASCII_WHITESPACE`.
    """
    if name == "ASCII_WHITESPACE":
        import warnings

        warnings.warn(
            "ASCII_WHITESPACE is deprecated because CommonMark v0.30 no longer "
            "defines ASCII whitespace.",
            DeprecationWarning,
            stacklevel=2,
        )
        return frozenset({chr(9), chr(10), chr(11), chr(12), chr(13), chr(32)})
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )  # pragma: no cover
