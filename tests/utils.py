from __future__ import annotations

import json
from typing import TYPE_CHECKING

from mdformat._cli import run
from mdformat._conf import read_toml_opts
from mdformat.renderer import RenderContext, RenderTreeNode

if TYPE_CHECKING:
    from markdown_it import MarkdownIt

UNFORMATTED_MARKDOWN = "\n\n# A header\n\n"
FORMATTED_MARKDOWN = "# A header\n"


def run_with_clear_cache(*args, **kwargs):
    read_toml_opts.cache_clear()
    return run(*args, **kwargs)


class JSONFormatterPlugin:
    """A code formatter plugin that formats JSON."""

    @staticmethod
    def format_json(unformatted: str, _info_str: str) -> str:
        parsed = json.loads(unformatted)
        return json.dumps(parsed, indent=2) + "\n"


class TextEditorPlugin:
    """A plugin that makes all text the same."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "All text is like this now!"

    RENDERERS = {"text": _text_renderer}


class TablePlugin:
    """A plugin that adds table extension to the parser."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    def _table_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "dummy 21"

    RENDERERS = {"table": _table_renderer}


class ASTChangingPlugin:
    """A plugin that makes AST breaking formatting changes."""

    CHANGES_AST = True

    TEXT_REPLACEMENT = "Content replaced completely. AST is now broken!"

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_renderer(  # type: ignore[misc]
        tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return ASTChangingPlugin.TEXT_REPLACEMENT

    RENDERERS = {"text": _text_renderer}


class PrefixPostprocessPlugin:
    """A plugin that postprocesses text, adding a prefix."""

    CHANGES_AST = True

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_postprocess(  # type: ignore[misc]
        text: str, tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return "Prefixed!" + text

    RENDERERS: dict = {}
    POSTPROCESSORS = {"text": _text_postprocess}


class SuffixPostprocessPlugin:
    """A plugin that postprocesses text, adding a suffix."""

    CHANGES_AST = True

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        pass

    def _text_postprocess(  # type: ignore[misc]
        text: str, tree: RenderTreeNode, context: RenderContext
    ) -> str:
        return text + "Suffixed!"

    RENDERERS: dict = {}
    POSTPROCESSORS = {"text": _text_postprocess}
