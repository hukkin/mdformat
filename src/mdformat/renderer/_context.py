from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator, Iterable, Mapping, MutableMapping
from contextlib import contextmanager
import functools
import logging
import re
import textwrap
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

from markdown_it.rules_block.html_block import HTML_SEQUENCES

from mdformat import codepoints
from mdformat._conf import DEFAULT_OPTS
from mdformat.renderer._util import (
    decimalify_leading,
    decimalify_trailing,
    escape_asterisk_emphasis,
    escape_less_than_sign,
    escape_square_brackets,
    escape_underscore_emphasis,
    get_list_marker_type,
    is_tight_list,
    is_tight_list_item,
    longest_consecutive_sequence,
    maybe_add_link_brackets,
    re_char_reference,
)

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode
    from mdformat.renderer.typing import Postprocess, Render

LOGGER = logging.getLogger(__name__)

# A marker used to point a location where word wrap is allowed
# to occur.
WRAP_POINT = "\x00"
# A marker used to indicate location of a character that should be preserved
# during word wrap. Should be converted to the actual character after wrap.
PRESERVE_CHAR = "\x00"
RE_PRESERVE_CHAR = re.compile(re.escape(PRESERVE_CHAR))

RE_UNICODE_WS_OR_WRAP_POINT = re.compile(
    rf"[{re.escape(''.join(codepoints.UNICODE_WHITESPACE))}]"
    "|"
    rf"{re.escape(WRAP_POINT)}+"
)


def make_render_children(separator: str) -> Render:
    def render_children(
        node: RenderTreeNode,
        context: RenderContext,
    ) -> str:
        render_outputs = (child.render(context) for child in node.children)
        return separator.join(out for out in render_outputs if out)

    return render_children


def hr(node: RenderTreeNode, context: RenderContext) -> str:
    thematic_break_width = 70
    return "_" * thematic_break_width


def code_inline(node: RenderTreeNode, context: RenderContext) -> str:
    code = node.content
    all_chars_are_whitespace = not code.strip()
    longest_backtick_seq = longest_consecutive_sequence(code, "`")
    if longest_backtick_seq:
        separator = "`" * (longest_backtick_seq + 1)
        return f"{separator} {code} {separator}"
    if code.startswith(" ") and code.endswith(" ") and not all_chars_are_whitespace:
        return f"` {code} `"
    return f"`{code}`"


def html_block(node: RenderTreeNode, context: RenderContext) -> str:
    content = node.content.rstrip("\n")
    # Need to strip leading spaces because we do so for regular Markdown too.
    # Without the stripping the raw HTML and Markdown get unaligned and
    # semantic may change.
    content = content.lstrip()
    return content


def html_inline(node: RenderTreeNode, context: RenderContext) -> str:
    return node.content


def _in_block(block_name: str, node: RenderTreeNode) -> bool:
    while node.parent:
        if node.parent.type == block_name:
            return True
        node = node.parent
    return False


def hardbreak(node: RenderTreeNode, context: RenderContext) -> str:
    if _in_block("heading", node):
        return "<br /> "
    return "\\" + "\n"


def softbreak(node: RenderTreeNode, context: RenderContext) -> str:
    if context.do_wrap and _in_block("paragraph", node):
        return WRAP_POINT
    return "\n"


def text(node: RenderTreeNode, context: RenderContext) -> str:
    """Process a text token.

    Text should always be a child of an inline token. An inline token
    should always be enclosed by a heading or a paragraph.
    """
    text = node.content

    # Convert tabs to spaces
    text = text.replace("\t", " ")
    # Reduce tabs and spaces to one space
    text = re.sub(" {2,}", " ", text)

    # Escape backslash to prevent it from making unintended escapes.
    # This escape has to be first, else we start multiplying backslashes.
    text = text.replace("\\", "\\\\")

    text = escape_asterisk_emphasis(text)  # Escape emphasis/strong marker.
    text = escape_underscore_emphasis(text)  # Escape emphasis/strong marker.
    # Escape link label and link ref enclosures
    text = escape_square_brackets(text, context.env["used_refs"])
    text = escape_less_than_sign(text)  # Escape URI enclosure and HTML.
    text = text.replace("`", "\\`")  # Escape code span marker

    # Escape "&" if it starts a sequence that can be interpreted as
    # a character reference.
    text = re_char_reference().sub(r"\\\g<0>", text)

    # The parser can give us consecutive newlines which can break
    # the markdown structure. Replace two or more consecutive newlines
    # with newline character's decimal reference.
    text = text.replace("\n\n", "&#10;&#10;")

    # If the last character is a "!" and the token next up is a link, we
    # have to escape the "!" or else the link will be interpreted as image.
    next_sibling = node.next_sibling
    if text.endswith("!") and next_sibling and next_sibling.type == "link":
        text = text[:-1] + "\\!"

    if context.do_wrap and _in_block("paragraph", node):
        text = re.sub(r"[ \t\n]+", WRAP_POINT, text)

    return text


def fence(node: RenderTreeNode, context: RenderContext) -> str:
    info_str = node.info.strip()
    lang = info_str.split(maxsplit=1)[0] if info_str else ""
    code_block = node.content

    # Info strings of backtick code fences cannot contain backticks.
    # If that is the case, we make a tilde code fence instead.
    fence_char = "~" if "`" in info_str else "`"

    # Format the code block using enabled codeformatter funcs
    fmt_func = context.options.get("codeformatters", {}).get(lang)
    if fmt_func:
        try:
            code_block = fmt_func(code_block, info_str)
        except Exception:
            # Swallow exceptions so that formatter errors (e.g. due to
            # invalid code) do not crash mdformat.
            assert node.map is not None, "A fence token must have `map` attribute set"
            filename = context.options.get("mdformat", {}).get("filename", "")
            warn_msg = (
                f"Failed formatting content of a {lang} code block "
                f"(line {node.map[0] + 1} before formatting)"
            )
            if filename:
                warn_msg += f". Filename: {filename}"
            LOGGER.warning(warn_msg)
        else:
            if code_block and code_block[-1] != "\n":
                code_block += "\n"

    # The code block must not include as long or longer sequence of `fence_char`s
    # as the fence string itself
    fence_len = max(3, longest_consecutive_sequence(code_block, fence_char) + 1)
    fence_str = fence_char * fence_len

    return f"{fence_str}{info_str}\n{code_block}{fence_str}"


def code_block(node: RenderTreeNode, context: RenderContext) -> str:
    return fence(node, context)


def image(node: RenderTreeNode, context: RenderContext) -> str:
    description = _render_inline_as_text(node, context)

    if context.do_wrap:
        # Prevent line breaks
        description = description.replace(WRAP_POINT, " ")

    ref_label = node.meta.get("label")
    if ref_label:
        context.env["used_refs"].add(ref_label)
        ref_label_repr = ref_label.lower()
        if description.lower() == ref_label_repr:
            return f"![{description}]"
        return f"![{description}][{ref_label_repr}]"

    uri = node.attrs["src"]
    assert isinstance(uri, str)
    uri = maybe_add_link_brackets(uri)
    title = node.attrs.get("title")
    if title is not None:
        return f'![{description}]({uri} "{title}")'
    return f"![{description}]({uri})"


def _render_inline_as_text(node: RenderTreeNode, context: RenderContext) -> str:
    """Special kludge for image `alt` attributes to conform CommonMark spec.

    Don't try to use it! Spec requires to show `alt` content with
    stripped markup, instead of simple escaping.
    """

    def text_renderer(node: RenderTreeNode, context: RenderContext) -> str:
        return node.content

    def image_renderer(node: RenderTreeNode, context: RenderContext) -> str:
        return _render_inline_as_text(node, context)

    inline_renderers: Mapping[str, Render] = defaultdict(
        lambda: make_render_children(""),
        {
            "text": text_renderer,
            "image": image_renderer,
            "link": link,
            "softbreak": softbreak,
        },
    )
    inline_context = RenderContext(
        inline_renderers, context.postprocessors, context.options, context.env
    )
    return make_render_children("")(node, inline_context)


def link(node: RenderTreeNode, context: RenderContext) -> str:
    if node.info == "auto":
        autolink_url = node.attrs["href"]
        assert isinstance(autolink_url, str)
        # The parser adds a "mailto:" prefix to autolink email href. We remove the
        # prefix if it wasn't there in the source.
        if autolink_url.startswith("mailto:") and not node.children[
            0
        ].content.startswith("mailto:"):
            autolink_url = autolink_url[7:]
        return "<" + autolink_url + ">"

    text = "".join(child.render(context) for child in node.children)

    if context.do_wrap:
        # Prevent line breaks
        text = text.replace(WRAP_POINT, " ")

    ref_label = node.meta.get("label")
    if ref_label:
        context.env["used_refs"].add(ref_label)
        ref_label_repr = ref_label.lower()
        if text.lower() == ref_label_repr:
            return f"[{text}]"
        return f"[{text}][{ref_label_repr}]"

    uri = node.attrs["href"]
    assert isinstance(uri, str)
    uri = maybe_add_link_brackets(uri)
    title = node.attrs.get("title")
    if title is None:
        return f"[{text}]({uri})"
    assert isinstance(title, str)
    title = title.replace('"', '\\"')
    return f'[{text}]({uri} "{title}")'


def em(node: RenderTreeNode, context: RenderContext) -> str:
    text = make_render_children(separator="")(node, context)
    indicator = node.markup
    return indicator + text + indicator


def strong(node: RenderTreeNode, context: RenderContext) -> str:
    text = make_render_children(separator="")(node, context)
    indicator = node.markup
    return indicator + text + indicator


def heading(node: RenderTreeNode, context: RenderContext) -> str:
    text = make_render_children(separator="")(node, context)

    if node.markup == "=":
        prefix = "# "
    elif node.markup == "-":
        prefix = "## "
    else:  # ATX heading
        prefix = node.markup + " "

    # There can be newlines in setext headers, but we make an ATX
    # header always. Convert newlines to spaces.
    text = text.replace("\n", " ")

    # If the text ends in a sequence of hashes (#), the hashes will be
    # interpreted as an optional closing sequence of the heading, and
    # will not be rendered. Escape a line ending hash to prevent this.
    if text.endswith("#"):
        text = text[:-1] + "\\#"

    return prefix + text


def blockquote(node: RenderTreeNode, context: RenderContext) -> str:
    marker = "> "
    with context.indented(len(marker)):
        text = make_render_children(separator="\n\n")(node, context)
        lines = text.splitlines()
        if not lines:
            return ">"
        quoted_lines = (f"{marker}{line}" if line else ">" for line in lines)
        quoted_str = "\n".join(quoted_lines)
        return quoted_str


@functools.lru_cache
def cached_textwrapper(width: int) -> textwrap.TextWrapper:
    return textwrap.TextWrapper(
        break_long_words=False,
        break_on_hyphens=False,
        width=width,
        expand_tabs=False,
        replace_whitespace=False,
    )


def _wrap(text: str, *, width: int | Literal["no"]) -> str:
    """Wrap text at locations pointed by `WRAP_POINT`s.

    Converts `WRAP_POINT`s to either a space or newline character, thus
    wrapping the text. Already existing whitespace will be preserved as
    is.
    """
    text, replacements = _prepare_wrap(text)
    if width == "no":
        return _recover_preserve_chars(text, replacements)

    wrapper = cached_textwrapper(width)
    wrapped = wrapper.fill(text)
    wrapped = _recover_preserve_chars(wrapped, replacements)
    return wrapped


def _prepare_wrap(text: str) -> tuple[str, list[str]]:
    """Prepare text for wrap.

    Convert `WRAP_POINT`s to spaces. Convert whitespace to
    `PRESERVE_CHAR`s. Return a tuple with the prepared string, and a
    list consisting of replacement characters for `PRESERVE_CHAR`s.
    """
    replacements = []

    def replacer(match: re.Match[str]) -> str:
        first_char = match.group()[0]
        if first_char == WRAP_POINT:
            return " "
        replacements.append(first_char)
        return PRESERVE_CHAR

    result = RE_UNICODE_WS_OR_WRAP_POINT.sub(replacer, text)
    return result, replacements


def _recover_preserve_chars(text: str, replacements: Iterable[str]) -> str:
    iter_replacements = iter(replacements)
    return RE_PRESERVE_CHAR.sub(lambda _: next(iter_replacements), text)


def paragraph(node: RenderTreeNode, context: RenderContext) -> str:  # noqa: C901
    inline_node = node.children[0]
    text = inline_node.render(context)

    if context.do_wrap:
        wrap_mode = context.options["mdformat"]["wrap"]
        if isinstance(wrap_mode, int):
            wrap_mode -= context.env["indent_width"]
            wrap_mode = max(1, wrap_mode)
        # Newlines should be mostly WRAP_POINTs by now, but there are
        # exceptional newlines that need to be preserved:
        # - hard breaks: newline defines the hard break
        # - html inline: newline vs space can be the difference between
        #                html block and html inline
        # Split the text and word wrap each section separately.
        sections = text.split("\n")
        text = "\n".join(_wrap(s, width=wrap_mode) for s in sections)

    # A paragraph can start or end in whitespace e.g. if the whitespace was
    # in decimal representation form. We need to re-decimalify it, one reason being
    # to enable "empty" paragraphs with whitespace only.
    text = decimalify_leading(codepoints.UNICODE_WHITESPACE, text)
    text = decimalify_trailing(codepoints.UNICODE_WHITESPACE, text)

    lines = text.split("\n")
    for i in range(len(lines)):
        # Strip whitespace to prevent issues like a line starting tab that is
        # interpreted as start of a code block.
        lines[i] = lines[i].strip()

        # If a line looks like an ATX heading, escape the first hash.
        if re.match(r"#{1,6}( |\t|$)", lines[i]):
            lines[i] = f"\\{lines[i]}"

        # Make sure a paragraph line does not start with ">"
        # (otherwise it will be interpreted as a block quote).
        if lines[i].startswith(">"):
            lines[i] = f"\\{lines[i]}"

        # Make sure a paragraph line does not start with "*", "-" or "+"
        # followed by a space, tab, or end of line.
        # (otherwise it will be interpreted as list item).
        if re.match(r"[-*+]( |\t|$)", lines[i]):
            lines[i] = f"\\{lines[i]}"

        # If a line starts with a number followed by "." or ")" followed by
        # a space, tab or end of line, escape the "." or ")" or it will be
        # interpreted as ordered list item.
        if re.match(r"[0-9]+\)( |\t|$)", lines[i]):
            lines[i] = lines[i].replace(")", "\\)", 1)
        if re.match(r"[0-9]+\.( |\t|$)", lines[i]):
            lines[i] = lines[i].replace(".", "\\.", 1)

        # Consecutive "-", "*" or "_" sequences can be interpreted as thematic
        # break. Escape them.
        space_removed = lines[i].replace(" ", "").replace("\t", "")
        if len(space_removed) >= 3:
            if all(c == "*" for c in space_removed):
                lines[i] = lines[i].replace("*", "\\*", 1)  # pragma: no cover
            elif all(c == "-" for c in space_removed):
                lines[i] = lines[i].replace("-", "\\-", 1)
            elif all(c == "_" for c in space_removed):
                lines[i] = lines[i].replace("_", "\\_", 1)  # pragma: no cover

        # A stripped line where all characters are "=" or "-" will be
        # interpreted as a setext heading. Escape.
        stripped = lines[i].strip(" \t")
        if all(c == "-" for c in stripped):
            lines[i] = lines[i].replace("-", "\\-", 1)
        elif all(c == "=" for c in stripped):
            lines[i] = lines[i].replace("=", "\\=", 1)

        # Check if the line could be interpreted as an HTML block.
        # If yes, prefix it with 4 spaces to prevent this.
        for html_seq_tuple in HTML_SEQUENCES:
            can_break_paragraph = html_seq_tuple[2]
            opening_re = html_seq_tuple[0]
            if can_break_paragraph and opening_re.search(lines[i]):
                lines[i] = f"    {lines[i]}"
                break

    text = "\n".join(lines)

    return text


def list_item(node: RenderTreeNode, context: RenderContext) -> str:
    """Return one list item as string.

    This returns just the content. List item markers and indentation are
    added in `bullet_list` and `ordered_list` renderers.
    """
    block_separator = "\n" if is_tight_list_item(node) else "\n\n"
    text = make_render_children(block_separator)(node, context)

    if not text.strip():
        return ""
    return text


def bullet_list(node: RenderTreeNode, context: RenderContext) -> str:
    marker_type = get_list_marker_type(node)
    first_line_indent = " "
    indent = " " * len(marker_type + first_line_indent)
    block_separator = "\n" if is_tight_list(node) else "\n\n"

    with context.indented(len(indent)):
        text = ""
        for child_idx, child in enumerate(node.children):
            list_item = child.render(context)
            formatted_lines = []
            line_iterator = iter(list_item.split("\n"))
            first_line = next(line_iterator)
            formatted_lines.append(
                f"{marker_type}{first_line_indent}{first_line}"
                if first_line
                else marker_type
            )
            for line in line_iterator:
                formatted_lines.append(f"{indent}{line}" if line else "")

            text += "\n".join(formatted_lines)
            if child_idx != len(node.children) - 1:
                text += block_separator

        return text


def ordered_list(node: RenderTreeNode, context: RenderContext) -> str:
    consecutive_numbering = context.options.get("mdformat", {}).get(
        "number", DEFAULT_OPTS["number"]
    )
    marker_type = get_list_marker_type(node)
    first_line_indent = " "
    block_separator = "\n" if is_tight_list(node) else "\n\n"
    list_len = len(node.children)

    starting_number = node.attrs.get("start")
    if starting_number is None:
        starting_number = 1
    assert isinstance(starting_number, int)

    if consecutive_numbering:
        indent_width = len(
            f"{list_len + starting_number - 1}{marker_type}{first_line_indent}"
        )
    else:
        indent_width = len(f"{starting_number}{marker_type}{first_line_indent}")

    text = ""
    with context.indented(indent_width):
        for list_item_index, list_item in enumerate(node.children):
            list_item_text = list_item.render(context)
            formatted_lines = []
            line_iterator = iter(list_item_text.split("\n"))
            first_line = next(line_iterator)
            if consecutive_numbering:
                # Prefix first line of the list item with consecutive numbering,
                # padded with zeros to make all markers of even length.
                # E.g.
                #   002. This is the first list item
                #   003. Second item
                #   ...
                #   112. Last item
                number = starting_number + list_item_index
                pad = len(str(list_len + starting_number - 1))
                number_str = str(number).rjust(pad, "0")
                formatted_lines.append(
                    f"{number_str}{marker_type}{first_line_indent}{first_line}"
                    if first_line
                    else f"{number_str}{marker_type}"
                )
            else:
                # Prefix first line of first item with the starting number of the
                # list. Prefix following list items with the number one
                # prefixed by zeros to make the list item marker of even length
                # with the first one.
                # E.g.
                #   5321. This is the first list item
                #   0001. Second item
                #   0001. Third item
                first_item_marker = f"{starting_number}{marker_type}"
                other_item_marker = (
                    "0" * (len(str(starting_number)) - 1) + "1" + marker_type
                )
                if list_item_index == 0:
                    formatted_lines.append(
                        f"{first_item_marker}{first_line_indent}{first_line}"
                        if first_line
                        else first_item_marker
                    )
                else:
                    formatted_lines.append(
                        f"{other_item_marker}{first_line_indent}{first_line}"
                        if first_line
                        else other_item_marker
                    )
            for line in line_iterator:
                formatted_lines.append(" " * indent_width + line if line else "")

            text += "\n".join(formatted_lines)
            if list_item_index != len(node.children) - 1:
                text += block_separator

        return text


DEFAULT_RENDERERS: Mapping[str, Render] = MappingProxyType(
    {
        "inline": make_render_children(""),
        "root": make_render_children("\n\n"),
        "hr": hr,
        "code_inline": code_inline,
        "html_block": html_block,
        "html_inline": html_inline,
        "hardbreak": hardbreak,
        "softbreak": softbreak,
        "text": text,
        "fence": fence,
        "code_block": code_block,
        "link": link,
        "image": image,
        "em": em,
        "strong": strong,
        "heading": heading,
        "blockquote": blockquote,
        "paragraph": paragraph,
        "bullet_list": bullet_list,
        "ordered_list": ordered_list,
        "list_item": list_item,
    }
)


class RenderContext(NamedTuple):
    """A collection of data that is passed as input to `Render` and
    `Postprocess` functions."""

    renderers: Mapping[str, Render]
    postprocessors: Mapping[str, Iterable[Postprocess]]
    options: Mapping[str, Any]
    env: MutableMapping

    @contextmanager
    def indented(self, width: int) -> Generator[None, None, None]:
        self.env["indent_width"] += width
        try:
            yield
        finally:
            self.env["indent_width"] -= width

    @property
    def do_wrap(self) -> bool:
        wrap_mode = self.options.get("mdformat", {}).get("wrap", DEFAULT_OPTS["wrap"])
        return isinstance(wrap_mode, int) or wrap_mode == "no"

    def with_default_renderer_for(self, *syntax_names: str) -> RenderContext:
        renderers = dict(self.renderers)
        for syntax in syntax_names:
            if syntax in DEFAULT_RENDERERS:
                renderers[syntax] = DEFAULT_RENDERERS[syntax]
            else:
                renderers.pop(syntax, None)
        return RenderContext(
            MappingProxyType(renderers), self.postprocessors, self.options, self.env
        )
