from __future__ import annotations

import argparse
from collections.abc import Generator, Iterable, Mapping, Sequence
import contextlib
import functools
import logging
import os.path
from pathlib import Path
import shutil
import sys
import textwrap

import mdformat
from mdformat._conf import DEFAULT_OPTS, InvalidConfError, read_toml_opts
from mdformat._util import detect_newline_type, is_md_equal
import mdformat.plugins


class RendererWarningPrinter(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:  # pragma: no branch
            sys.stderr.write(f"Warning: {record.msg}\n")


def run(cli_args: Sequence[str], cache_toml: bool = True) -> int:  # noqa: C901
    arg_parser = make_arg_parser(
        mdformat.plugins._PARSER_EXTENSION_DISTS,
        mdformat.plugins._CODEFORMATTER_DISTS,
        mdformat.plugins.PARSER_EXTENSIONS,
    )
    cli_opts = {
        k: v for k, v in vars(arg_parser.parse_args(cli_args)).items() if v is not None
    }
    cli_core_opts, cli_plugin_opts = separate_core_and_plugin_opts(cli_opts)

    if not cli_opts["paths"]:
        print_paragraphs(["No files have been passed in. Doing nothing."])
        return 0

    try:
        file_paths = resolve_file_paths(cli_opts["paths"])
    except InvalidPath as e:
        arg_parser.error(f'File "{e.path}" does not exist.')

    format_errors_found = False
    renderer_warning_printer = RendererWarningPrinter()
    for path in file_paths:
        read_toml = read_toml_opts if cache_toml else read_toml_opts.__wrapped__
        try:
            toml_opts, toml_path = read_toml(path.parent if path else Path.cwd())
        except InvalidConfError as e:
            print_error(str(e))
            return 1

        opts = {**DEFAULT_OPTS, **toml_opts, **cli_core_opts}

        # Merge plugin options from CLI.
        # Make a copy of opts["plugin"] to not mutate DEFAULT_OPTS or cached TOML.
        opts["plugin"] = dict(opts["plugin"])
        for plugin_id, plugin_opts in cli_plugin_opts.items():
            if plugin_id in opts["plugin"]:
                opts["plugin"][plugin_id] |= plugin_opts
            else:
                opts["plugin"][plugin_id] = plugin_opts

        if sys.version_info >= (3, 13):  # pragma: >=3.13 cover
            if is_excluded(path, opts["exclude"], toml_path, "exclude" in cli_opts):
                continue
        else:  # pragma: <3.13 cover
            if "exclude" in toml_opts:
                print_error(
                    "'exclude' patterns are only available on Python 3.13+.",
                    paragraphs=[
                        "Please remove the 'exclude' list from your .mdformat.toml"
                        " or upgrade Python version."
                    ],
                )
                return 1

        try:
            enabled_parserplugins = (
                mdformat.plugins.PARSER_EXTENSIONS
                if opts["extensions"] is None
                else {
                    k: mdformat.plugins.PARSER_EXTENSIONS[k] for k in opts["extensions"]
                }
            )
        except KeyError as e:
            print_error(
                "Invalid extension required.",
                paragraphs=[
                    f"The required {e.args[0]!r} extension is not available. "
                    "Please install a plugin that adds the extension, "
                    "or remove it from required extensions."
                ],
            )
            return 1
        try:
            enabled_codeformatters = (
                mdformat.plugins.CODEFORMATTERS
                if opts["codeformatters"] is None
                else {
                    k: mdformat.plugins.CODEFORMATTERS[k]
                    for k in opts["codeformatters"]
                }
            )
        except KeyError as e:
            print_error(
                "Invalid code formatter required.",
                paragraphs=[
                    f"The required {e.args[0]!r} code formatter language "
                    "is not available. "
                    "Please install a plugin "
                    "that adds support for the language, "
                    "or remove it from required languages."
                ],
            )
            return 1
        if path:
            path_str = str(path)
            # Unlike `path.read_text(encoding="utf-8")`, this preserves
            # line ending type.
            original_str = path.read_bytes().decode()
        else:
            path_str = "-"
            original_str = sys.stdin.read()

        # Lazy import to improve module import time
        from mdformat.renderer import LOGGER as RENDERER_LOGGER

        formatted_str = mdformat.text(
            original_str,
            options=opts,
            extensions=enabled_parserplugins,
            codeformatters=enabled_codeformatters,
            _first_pass_contextmanager=log_handler_applied(
                RENDERER_LOGGER, renderer_warning_printer
            ),
            _filename=path_str,
        )
        newline = detect_newline_type(original_str, opts["end_of_line"])
        formatted_str = formatted_str.replace("\n", newline)

        if opts["check"]:
            if formatted_str != original_str:
                format_errors_found = True
                print_error(f'File "{path_str}" is not formatted.')
        else:
            changes_ast = any(
                getattr(plugin, "CHANGES_AST", False)
                for plugin in enabled_parserplugins.values()
            )
            if (
                opts["validate"]
                and not changes_ast
                and not is_md_equal(
                    original_str,
                    formatted_str,
                    options=opts,
                    extensions=enabled_parserplugins,
                    codeformatters=enabled_codeformatters,
                )
            ):
                print_error(
                    f'Could not format "{path_str}".',
                    paragraphs=[
                        "Formatted Markdown renders to different HTML than input Markdown. "  # noqa: E501
                        "This is a bug in mdformat or one of its installed plugins. "
                        "Please retry without any plugins installed. "
                        "If this error persists, "
                        "report an issue including the input Markdown "
                        "on https://github.com/hukkin/mdformat/issues. "
                        "If not, "
                        "report an issue on the malfunctioning plugin's issue tracker.",
                    ],
                )
                return 1
            if path:
                if formatted_str != original_str:
                    path.write_bytes(formatted_str.encode())
            else:
                sys.stdout.buffer.write(formatted_str.encode())
    if format_errors_found:
        return 1
    return 0


def validate_wrap_arg(value: str) -> str | int:
    if value in {"keep", "no"}:
        return value
    width = int(value)
    if width < 1:
        raise ValueError("wrap width must be a positive integer")
    return width


def make_arg_parser(
    parser_extension_dists: Mapping[str, tuple[str, list[str]]],
    codeformatter_dists: Mapping[str, tuple[str, list[str]]],
    parser_extensions: Mapping[str, mdformat.plugins.ParserExtensionInterface],
) -> argparse.ArgumentParser:
    epilog = get_plugin_info_str(parser_extension_dists, codeformatter_dists)
    parser = argparse.ArgumentParser(
        description="CommonMark compliant Markdown formatter",
        epilog=(epilog if epilog else None),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="files to format")
    parser.add_argument(
        "--check", action="store_true", help="do not apply changes to files"
    )
    parser.add_argument(
        "--no-validate",
        action="store_const",
        const=False,
        dest="validate",
        help="do not validate that the rendered HTML is consistent",
    )
    version_str = f"mdformat {mdformat.__version__}"
    plugin_version_str = get_plugin_version_str(
        {**parser_extension_dists, **codeformatter_dists}
    )
    if plugin_version_str:
        version_str += f" ({plugin_version_str})"
    parser.add_argument("--version", action="version", version=version_str)
    parser.add_argument(
        "--number",
        action="store_const",
        const=True,
        help="apply consecutive numbering to ordered lists",
    )
    parser.add_argument(
        "--wrap",
        type=validate_wrap_arg,
        metavar="{keep,no,INTEGER}",
        help="paragraph word wrap mode (default: keep)",
    )
    parser.add_argument(
        "--end-of-line",
        choices=("lf", "crlf", "keep"),
        help="output file line ending mode (default: lf)",
    )
    if sys.version_info >= (3, 13):  # pragma: >=3.13 cover
        parser.add_argument(
            "--exclude",
            action="append",
            metavar="PATTERN",
            help="exclude files that match the Unix-style glob pattern "
            "(multiple allowed)",
        )
    extensions_group = parser.add_mutually_exclusive_group()
    extensions_group.add_argument(
        "--extensions",
        action="append",
        metavar="EXTENSION",
        help="require and enable an extension plugin "
        "(multiple allowed) "
        "(use `--no-extensions` to disable) "
        "(default: all enabled)",
    )
    extensions_group.add_argument(
        "--no-extensions",
        action="store_const",
        const=(),
        dest="extensions",
        help=argparse.SUPPRESS,
    )
    codeformatters_group = parser.add_mutually_exclusive_group()
    codeformatters_group.add_argument(
        "--codeformatters",
        action="append",
        metavar="LANGUAGE",
        help="require and enable a code formatter plugin "
        "(multiple allowed) "
        "(use `--no-codeformatters` to disable) "
        "(default: all enabled)",
    )
    codeformatters_group.add_argument(
        "--no-codeformatters",
        action="store_const",
        const=(),
        dest="codeformatters",
        help=argparse.SUPPRESS,
    )
    for plugin in parser_extensions.values():
        if hasattr(plugin, "add_cli_options"):
            import warnings

            plugin_file, plugin_line = get_source_file_and_line(plugin)
            warnings.warn_explicit(
                "`mdformat.plugins.ParserExtensionInterface.add_cli_options`"
                " is deprecated."
                " Please use `add_cli_argument_group`.",
                DeprecationWarning,
                filename=plugin_file,
                lineno=plugin_line,
            )
            plugin.add_cli_options(parser)
    for plugin_id, plugin in parser_extensions.items():
        if hasattr(plugin, "add_cli_argument_group"):
            group = parser.add_argument_group(title=f"{plugin_id} plugin")
            plugin.add_cli_argument_group(group)
            for action in group._group_actions:
                action.dest = f"plugin.{plugin_id}.{action.dest}"
    return parser


def separate_core_and_plugin_opts(opts: Mapping) -> tuple[dict, dict]:
    """Move dotted keys like 'plugin.gfm.some_key' to a separate mapping.

    Return a tuple of two mappings. First is for core CLI options, the
    second for plugin options. E.g. 'plugin.gfm.some_key' belongs to the
    second mapping under {"gfm": {"some_key": <value>}}.
    """
    cli_core_opts = {}
    cli_plugin_opts: dict = {}
    for k, v in opts.items():
        if k.startswith("plugin."):
            _, plugin_id, plugin_conf_key = k.split(".", maxsplit=2)
            if plugin_id in cli_plugin_opts:
                cli_plugin_opts[plugin_id][plugin_conf_key] = v
            else:
                cli_plugin_opts[plugin_id] = {plugin_conf_key: v}
        else:
            cli_core_opts[k] = v
    return cli_core_opts, cli_plugin_opts


class InvalidPath(Exception):
    """Exception raised when a path does not exist."""

    def __init__(self, path: Path):
        self.path = path


def resolve_file_paths(path_strings: Iterable[str]) -> list[None | Path]:
    """Resolve pathlib.Path objects from filepath strings.

    Convert path strings to pathlib.Path objects. Check that all paths
    are either files, directories or stdin. If not, raise InvalidPath.
    Resolve directory paths to a list of file paths (ending with ".md").
    """
    file_paths: list[None | Path] = []  # Path to file or None for stdin/stdout
    for path_str in path_strings:
        if path_str == "-":
            file_paths.append(None)
            continue
        path_obj = Path(path_str)
        path_obj = _normalize_path(path_obj)
        if path_obj.is_dir():
            for p in path_obj.glob("**/*.md"):
                if p.is_file():
                    p = _normalize_path(p)
                    file_paths.append(p)
        elif path_obj.is_file():  # pragma: nt no cover
            file_paths.append(path_obj)
        else:  # pragma: nt no cover
            raise InvalidPath(path_obj)
    return file_paths


def is_excluded(  # pragma: >=3.13 cover
    path: Path | None,
    patterns: list[str],
    toml_path: Path | None,
    excludes_from_cli: bool,
) -> bool:
    if not path:
        return False

    if not excludes_from_cli and toml_path:
        exclude_root = toml_path.parent
    else:
        exclude_root = Path.cwd()

    try:
        relative_path = path.relative_to(exclude_root)
    except ValueError:
        return False

    return any(
        relative_path.full_match(pattern)  # type: ignore[attr-defined]
        for pattern in patterns
    )


def _normalize_path(path: Path) -> Path:
    """Normalize path.

    Make the path absolute, resolve any ".." sequences. Do not resolve
    symlinks, as it would interfere with 'exclude' patterns. Raise
    `InvalidPath` if the path does not exist.
    """
    path = Path(os.path.abspath(path))
    try:
        path_exists = path.exists()
    except OSError:  # Catch "OSError: [WinError 123]" on Windows  # pragma: no cover
        path_exists = False
    if not path_exists:
        raise InvalidPath(path)
    return path


def print_paragraphs(paragraphs: Iterable[str]) -> None:
    assert not isinstance(paragraphs, str)
    sys.stderr.write(wrap_paragraphs(paragraphs))


def print_error(title: str, paragraphs: Iterable[str] = ()) -> None:
    assert not isinstance(paragraphs, str)
    assert not title.lower().startswith("error")
    title = "Error: " + title
    paragraphs = [title] + list(paragraphs)
    print_paragraphs(paragraphs)


@functools.lru_cache
def cached_textwrapper(width: int) -> textwrap.TextWrapper:
    return textwrap.TextWrapper(
        break_long_words=False,
        break_on_hyphens=False,
        width=width,
        expand_tabs=False,
        replace_whitespace=False,
    )


def wrap_paragraphs(paragraphs: Iterable[str]) -> str:
    """Wrap and concatenate paragraphs.

    Take an iterable of paragraphs as input. Return a string where the
    paragraphs are concatenated (empty line as separator) and wrapped.
    End the string in a newline.
    """
    terminal_width, _ = shutil.get_terminal_size()
    if 0 < terminal_width < 80:
        wrap_width = terminal_width
    else:
        wrap_width = 80
    wrapper = cached_textwrapper(wrap_width)
    return "\n\n".join(wrapper.fill(p) for p in paragraphs) + "\n"


@contextlib.contextmanager
def log_handler_applied(
    logger: logging.Logger, handler: logging.Handler
) -> Generator[None, None, None]:
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)


def get_plugin_info_str(
    parser_extension_dists: Mapping[str, tuple[str, list[str]]],
    codeformatter_dists: Mapping[str, tuple[str, list[str]]],
) -> str:
    info = ""
    if codeformatter_dists:
        info += "installed codeformatters:"
        for dist, dist_info in codeformatter_dists.items():
            langs = ", ".join(dist_info[1])
            info += f"\n  {dist}: {langs}"
    if parser_extension_dists:
        if info:
            info += "\n\n"
        info += "installed extensions:"
        for dist, dist_info in parser_extension_dists.items():
            extensions = ", ".join(dist_info[1])
            info += f"\n  {dist}: {extensions}"
    return info


def get_plugin_version_str(dist_map: Mapping[str, tuple[str, list[str]]]) -> str:
    return ", ".join(
        f"{dist_name} {dist_info[0]}" for dist_name, dist_info in dist_map.items()
    )


def get_source_file_and_line(obj: object) -> tuple[str, int]:
    import inspect

    try:
        filename = inspect.getsourcefile(obj)  # type: ignore[arg-type]
        if filename is None:  # pragma: no cover
            filename = "not found"
    except TypeError:  # pragma: no cover
        filename = "built-in object"
    try:
        _, lineno = inspect.getsourcelines(obj)  # type: ignore[arg-type]
    except (OSError, TypeError):  # pragma: no cover
        lineno = 0
    return filename, lineno
