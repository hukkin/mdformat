from __future__ import annotations

from collections.abc import Iterable
import functools
import html.entities
import re
from typing import TYPE_CHECKING

from mdformat import codepoints

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode


@functools.cache
def re_char_reference() -> re.Pattern[str]:
    """Return a regex that finds character references.

    The reference can be either:
    1. decimal representation, e.g. &#11;
    2. hex representation, e.g. &#x1e;
    3. HTML5 entity reference, e.g. &nbsp;

    This cached function compiles the regex lazily,
    as compilation can take over 20ms.
    """
    return re.compile(
        "&(?:"
        + "#[0-9]{1,7}"
        + "|"
        + "#[Xx][0-9A-Fa-f]{1,6}"
        + "|"
        + "|".join({c.rstrip(";") for c in html.entities.html5})
        + ");"
    )


def is_tight_list(node: RenderTreeNode) -> bool:
    assert node.type in {"bullet_list", "ordered_list"}

    # The list has list items at level +1 so paragraphs in those list
    # items must be at level +2 (grand children)
    for child in node.children:
        for grand_child in child.children:
            if grand_child.type != "paragraph":
                continue
            is_tight = grand_child.hidden
            if not is_tight:
                return False
    return True


def is_tight_list_item(node: RenderTreeNode) -> bool:
    assert node.type == "list_item"
    assert node.parent is not None
    return is_tight_list(node.parent)


def longest_consecutive_sequence(seq: str, char: str) -> int:
    """Return length of the longest consecutive sequence of `char` characters
    in string `seq`."""
    assert len(char) == 1
    longest = 0
    current_streak = 0
    for c in seq:
        if c == char:
            current_streak += 1
        else:
            current_streak = 0
        if current_streak > longest:
            longest = current_streak
    return longest


def maybe_add_link_brackets(link: str) -> str:
    """Surround URI with brackets if required by spec."""
    if not link or (codepoints.ASCII_CTRL | {" ", "(", ")"}).intersection(link):
        return "<" + link + ">"
    return link


def get_list_marker_type(node: RenderTreeNode) -> str:
    if node.type == "bullet_list":
        mode = "bullet"
        primary_marker = "-"
        secondary_marker = "*"
    else:
        mode = "ordered"
        primary_marker = "."
        secondary_marker = ")"
    consecutive_lists_count = 1
    current = node
    while True:
        previous_sibling = current.previous_sibling
        if previous_sibling is None:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker
        prev_type = previous_sibling.type
        if (mode == "bullet" and prev_type == "bullet_list") or (
            mode == "ordered" and prev_type == "ordered_list"
        ):
            consecutive_lists_count += 1
            current = previous_sibling
        else:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker


def escape_asterisk_emphasis(text: str) -> str:
    """Escape asterisks to prevent unexpected emphasis/strong emphasis.

    Currently we escape all asterisks unless both previous and next
    character are Unicode whitespace.
    """
    # Fast exit to improve performance
    if "*" not in text:
        return text

    escaped_text = ""

    text_length = len(text)
    for i, current_char in enumerate(text):
        if current_char != "*":
            escaped_text += current_char
            continue
        prev_char = text[i - 1] if (i - 1) >= 0 else None
        next_char = text[i + 1] if (i + 1) < text_length else None
        if (
            prev_char in codepoints.UNICODE_WHITESPACE
            and next_char in codepoints.UNICODE_WHITESPACE
        ):
            escaped_text += current_char
            continue
        escaped_text += "\\" + current_char

    return escaped_text


def escape_underscore_emphasis(text: str, *, escape_openers: bool = False) -> str:
    """Escape underscores that could be interpreted as emphasis/strong
    emphasis.

    Emphasis needs both an opening and a closing delimiter, so escaping every
    underscore run that can *close* emphasis is enough to keep all underscores
    literal. Per CommonMark section 6.2 an underscore run can close emphasis
    only when it is preceded by a non-whitespace character and not followed by
    a word character (and can open emphasis in the mirror case). Runs that can
    neither open nor close emphasis, e.g. intraword underscores, stay literal.

    The characters bordering this text (the start and end of the string) belong
    to sibling nodes we cannot see here, so a run touching either end is escaped
    regardless. When the text is wrapped by ``_`` emphasis markers those markers
    can themselves pair with an inner run, so ``escape_openers`` additionally
    escapes runs that can only open, keeping the wrapped text intact.
    """
    # Fast exit to improve performance
    if "_" not in text:
        return text

    non_word_chars = codepoints.UNICODE_WHITESPACE | codepoints.UNICODE_PUNCTUATION
    escaped_text = ""

    text_length = len(text)
    i = 0
    while i < text_length:
        current_char = text[i]
        if current_char != "_":
            escaped_text += current_char
            i += 1
            continue
        run_start = i
        while i < text_length and text[i] == "_":
            i += 1
        prev_char = text[run_start - 1] if run_start else None
        next_char = text[i] if i < text_length else None
        left_nonspace = (
            prev_char is not None and prev_char not in codepoints.UNICODE_WHITESPACE
        )
        right_nonspace = (
            next_char is not None and next_char not in codepoints.UNICODE_WHITESPACE
        )
        left_word = prev_char is not None and prev_char not in non_word_chars
        right_word = next_char is not None and next_char not in non_word_chars
        can_close = left_nonspace and not right_word
        can_open = right_nonspace and not left_word
        at_border = prev_char is None or next_char is None
        escape = at_border or can_close or (escape_openers and can_open)
        if escape:
            escaped_text += "\\_" * (i - run_start)
        else:
            escaped_text += text[run_start:i]

    return escaped_text


def decimalify_leading(char_set: Iterable[str], text: str) -> str:
    """Replace first character with decimal representation if it's included in
    `char_set`."""
    if not char_set or not text:
        return text
    first_char = text[0]
    if first_char in char_set:
        return f"&#{ord(first_char)};{text[1:]}"
    return text


def decimalify_trailing(char_set: Iterable[str], text: str) -> str:
    """Replace last character with decimal representation if it's included in
    `char_set`."""
    if not char_set or not text:
        return text
    last_char = text[-1]
    if last_char in char_set:
        return f"{text[:-1]}&#{ord(last_char)};"
    return text


def split_at_indexes(text: str, indexes: Iterable[int]) -> list[str]:
    """Return the text in parts.

    Make splits right before the indexed character.
    """
    if not indexes:
        raise ValueError("indexes must not be empty")
    parts = []
    prev_i = 0
    for i in sorted(indexes):
        parts.append(text[prev_i:i])
        prev_i = i
    parts.append(text[i:])
    return parts


def escape_square_brackets(text: str, used_refs: Iterable[str]) -> str:
    """Return the input string with square brackets ("[" and "]") escaped in a
    safe way that avoids unintended link labels or refs after formatting.

    Heuristic to use:
    Escape all square brackets unless all the following are true for
    a closed pair of brackets ([ + text + ]):
    - the brackets enclose text containing no square brackets
    - the text is not a used_ref (a link label used in a valid link or image)
    - the enclosure is not followed by ":" or "(" (I believe that this, rather
      than requiring the enclosure to be followed by a character other than
      ":" or "(", should be sufficient, as no inline other than 'text' can
      start with ":" or "(", and a following text inline never exists as it
      would be included in the same token.
    """
    escape_before_pos = []
    pos = 0
    enclosure_start: int | None = None
    while True:
        bracket_match = RE_SQUARE_BRACKET.search(text, pos)
        if not bracket_match:
            if enclosure_start is not None:
                escape_before_pos.append(enclosure_start)
            break

        bracket = bracket_match.group()
        bracket_pos = bracket_match.start()
        pos = bracket_pos + 1
        if bracket == "[":
            if enclosure_start is not None:
                escape_before_pos.append(enclosure_start)
            enclosure_start = bracket_pos
        else:
            if enclosure_start is None:
                escape_before_pos.append(bracket_pos)
            else:
                enclosed = text[enclosure_start + 1 : bracket_pos]
                next_char = text[bracket_pos + 1 : bracket_pos + 2]  # can be empty str
                if enclosed.upper() not in used_refs and next_char not in {":", "("}:
                    enclosure_start = None
                else:
                    escape_before_pos.append(enclosure_start)
                    escape_before_pos.append(bracket_pos)
                    enclosure_start = None
    if not escape_before_pos:
        return text
    return "\\".join(split_at_indexes(text, escape_before_pos))


RE_SQUARE_BRACKET = re.compile(r"[\[\]]")


def escape_less_than_sign(text: str) -> str:
    """Escape less than sign ('<') to prevent unexpected HTML or autolink.

    Current heuristic to use: Always escape, except when
    - followed by a space: This should be safe. Neither HTML nor autolink
      allow space after the '<' sign
    """
    return RE_LESS_THAN_SIGN__NO_FOLLOWING_SPACE.sub(r"\\\g<0>", text)


RE_LESS_THAN_SIGN__NO_FOLLOWING_SPACE = re.compile("<(?:[^ ]|$)")
