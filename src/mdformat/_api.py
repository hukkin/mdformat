from __future__ import annotations

from collections.abc import Iterable, Mapping
from contextlib import AbstractContextManager
from os import PathLike
from pathlib import Path
from typing import Any

from mdformat._conf import DEFAULT_OPTS
from mdformat._util import EMPTY_MAP, NULL_CTX, build_mdit, detect_newline_type


def text(
    md: str,
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
    _first_pass_contextmanager: AbstractContextManager = NULL_CTX,
    _filename: str = "",
) -> str:
    """Format a Markdown string."""
    # Lazy import to improve module import time
    from mdformat.renderer import MDRenderer

    with _first_pass_contextmanager:
        mdit = build_mdit(
            MDRenderer,
            mdformat_opts={**options, **{"filename": _filename}},
            extensions=extensions,
            codeformatters=codeformatters,
        )
        rendering = mdit.render(md)

    # If word wrap is changed, add a second pass of rendering.
    # Some escapes will be different depending on word wrap, so
    # rendering after 1st and 2nd pass will be different. Rendering
    # twice seems like the easiest way to achieve stable formatting.
    if options.get("wrap", DEFAULT_OPTS["wrap"]) != "keep":
        rendering = mdit.render(rendering)

    return rendering


def file(
    f: str | PathLike[str],
    *,
    options: Mapping[str, Any] = EMPTY_MAP,
    extensions: Iterable[str] = (),
    codeformatters: Iterable[str] = (),
) -> None:
    """Format a Markdown file in place."""
    f = Path(f)
    try:
        is_file = f.is_file()
    except OSError:  # Catch "OSError: [WinError 123]" on Windows  # pragma: no cover
        is_file = False
    if not is_file:
        raise ValueError(f'Cannot format "{f}". It is not a file.')
    if f.is_symlink():
        raise ValueError(f'Cannot format "{f}". It is a symlink.')

    original_md = f.read_bytes().decode()
    formatted_md = text(
        original_md,
        options=options,
        extensions=extensions,
        codeformatters=codeformatters,
        _filename=str(f),
    )
    newline = detect_newline_type(
        original_md, options.get("end_of_line", DEFAULT_OPTS["end_of_line"])
    )
    formatted_md = formatted_md.replace("\n", newline)
    if formatted_md != original_md:
        f.write_bytes(formatted_md.encode())
