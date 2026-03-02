from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import nullcontext
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import mdformat.plugins

if TYPE_CHECKING:
    from markdown_it import MarkdownIt

NULL_CTX = nullcontext()
EMPTY_MAP: MappingProxyType = MappingProxyType({})

RE_NEWLINES = re.compile(r"\r\n|\r|\n")
RE_HTML_START_SPACE_PREFIX = re.compile(r" (<[a-zA-Z][-a-zA-Z0-9]*>)")
RE_HTML_END_SPACE_SUFFIX = re.compile(r"(</[a-zA-Z][-a-zA-Z0-9]*>) ")


def build_mdit(
    renderer_cls: Any,
    *,
    mdformat_opts: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> MarkdownIt:
    # Lazy import to improve module import time
    from markdown_it import MarkdownIt

    mdit = MarkdownIt(renderer_cls=renderer_cls)
    mdit.options["mdformat"] = mdformat_opts
    # store reference labels in link/image tokens
    mdit.options["store_labels"] = True

    mdit.options["parser_extension"] = []
    for name in extensions:
        plugin = mdformat.plugins.PARSER_EXTENSIONS[name]
        if plugin not in mdit.options["parser_extension"]:
            mdit.options["parser_extension"].append(plugin)
            plugin.update_mdit(mdit)

    mdit.options["codeformatters"] = {
        lang: mdformat.plugins.CODEFORMATTERS[lang] for lang in codeformatters
    }

    return mdit


# Chars that markdown-it-py escapes when rendering code_inline:
# https://github.com/executablebooks/markdown-it-py/blob/c5161b550f3c6c0a98d77e8389872405e8f9f9ee/markdown_it/common/utils.py#L138
# Note that "&" is not included as it is used in the escape sequences of
# these characters.
_invalid_html_code_chars = '<>"'
# a regex str that matches all except above chars
_valid_html_code_char_re = rf"[^{re.escape(_invalid_html_code_chars)}]"


def is_md_equal(
    md1: str,
    md2: str,
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> bool:
    """Check if two Markdown produce the same HTML.

    Renders HTML from both Markdown strings, reduces consecutive
    whitespace to a single space and checks equality. Note that this is
    not a perfect solution, as there can be meaningful whitespace in
    HTML, e.g. in a <code> block.
    """
    # Lazy import to improve module import time
    from markdown_it.renderer import RendererHTML

    html_texts = {}
    mdit = build_mdit(RendererHTML, mdformat_opts=options, extensions=extensions)
    for key, text in [("md1", md1), ("md2", md2)]:
        html = mdit.render(text)

        # Remove codeblocks because code formatter plugins do arbitrary changes.
        if codeformatters:
            langs_re = "|".join(re.escape(lang) for lang in codeformatters)
            html = re.sub(
                rf'<code class="language-(?:{langs_re})">'
                rf"{_valid_html_code_char_re}*"
                r"</code>",
                "",
                html,
            )

        # Reduce all whitespace to a single space
        html = re.sub(r"\s+", " ", html)

        # Strip insignificant paragraph leading/trailing whitespace
        html = html.replace("<p> ", "<p>")
        html = html.replace(" </p>", "</p>")

        # Also remove whitespace preceding opening tags, and trailing
        # closing tags, so that we can safely remove empty paragraphs
        # below without introducing extra whitespace.
        html = RE_HTML_END_SPACE_SUFFIX.sub(r"\g<1>", html)
        html = RE_HTML_START_SPACE_PREFIX.sub(r"\g<1>", html)

        # empty p elements should be ignored by user agents
        # (https://www.w3.org/TR/REC-html40/struct/text.html#edef-P)
        html = html.replace("<p></p>", "")

        # Leading and trailing whitespace should be safe to ignore. This
        # also makes any documents that are whitespace-only equal.
        html = html.strip()

        html_texts[key] = html

    return html_texts["md1"] == html_texts["md2"]


def detect_newline_type(md: str, eol_setting: str) -> Literal["\n", "\r\n"]:
    """Returns the newline-character to be used for output.

    If `eol_setting == "keep"`, the newline character used in the passed
    markdown is detected and returned. Otherwise the character matching
    the passed setting is returned.
    """
    if eol_setting == "keep":
        first_eol = RE_NEWLINES.search(md)
        return "\r\n" if first_eol and first_eol.group() == "\r\n" else "\n"
    if eol_setting == "crlf":
        return "\r\n"
    return "\n"
