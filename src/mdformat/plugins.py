from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, Protocol

from mdformat._compat import importlib_metadata

if TYPE_CHECKING:
    from markdown_it import MarkdownIt

    from mdformat.renderer.typing import Postprocess, Render


def _load_entrypoints(
    eps: importlib_metadata.EntryPoints,
) -> tuple[dict[str, Any], dict[str, tuple[str, list[str]]]]:
    loaded_ifaces: dict[str, Any] = {}
    dist_versions: dict[str, tuple[str, list[str]]] = {}
    for ep in eps:
        assert ep.dist, (
            "EntryPoint.dist should never be None "
            "when coming from Distribution.entry_points"
        )
        loaded_ifaces[ep.name] = ep.load()
        dist_name = ep.dist.name
        if dist_name in dist_versions:
            dist_versions[dist_name][1].append(ep.name)
        else:
            dist_versions[dist_name] = (ep.dist.version, [ep.name])
    return loaded_ifaces, dist_versions


CODEFORMATTERS: Mapping[str, Callable[[str, str], str]]
_CODEFORMATTER_DISTS: Mapping[str, tuple[str, list[str]]]
CODEFORMATTERS, _CODEFORMATTER_DISTS = _load_entrypoints(
    importlib_metadata.entry_points(group="mdformat.codeformatter")
)


class ParserExtensionInterface(Protocol):
    """An interface for parser extension plugins."""

    # Does the plugin's formatting change Markdown AST or not?
    # (optional, default: False)
    CHANGES_AST: bool = False

    # A mapping from `RenderTreeNode.type` to a `Render` function that can
    # render the given `RenderTreeNode` type. These override the default
    # `Render` funcs defined in `mdformat.renderer.DEFAULT_RENDERERS`.
    RENDERERS: Mapping[str, Render]

    # A mapping from `RenderTreeNode.type` to a `Postprocess` that does
    # postprocessing for the output of the `Render` function. Unlike
    # `Render` funcs, `Postprocess` funcs are collaborative: any number of
    # plugins can define a postprocessor for a syntax type and all of them
    # will run in series.
    # (optional)
    POSTPROCESSORS: Mapping[str, Postprocess]

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        """DEPRECATED - use `add_cli_argument_group` instead.

        Add options to the mdformat CLI, to be stored in
        mdit.options["mdformat"] (optional)
        """

    @staticmethod
    def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
        """Add an argument group to mdformat CLI and add arguments to it.

        Call `group.add_argument()` to add CLI arguments (signature is
        the same as argparse.ArgumentParser.add_argument). Values will be
        stored in a mapping under mdit.options["mdformat"]["plugin"][<plugin_id>]
        where <plugin_id> equals entry point name of the plugin.

        The mapping will be merged with values read from TOML config file
        section [plugin.<plugin_id>].

        (optional)
        """

    @staticmethod
    def update_mdit(mdit: MarkdownIt) -> None:
        """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""


PARSER_EXTENSIONS: Mapping[str, ParserExtensionInterface]
_PARSER_EXTENSION_DISTS: Mapping[str, tuple[str, list[str]]]
PARSER_EXTENSIONS, _PARSER_EXTENSION_DISTS = _load_entrypoints(
    importlib_metadata.entry_points(group="mdformat.parser_extension")
)
