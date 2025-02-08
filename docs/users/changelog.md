# Changelog

This log documents all Python API or CLI breaking backwards incompatible changes.
Note that there is currently no guarantee for a stable Markdown formatting style across versions.

## Develop

- Use consistent encoding when reading from stdin.
  It is now read with UTF-8 encoding, consistent with the encoding used in writing.

## 0.7.22

- Performance
  - Improved import time and performance of CLI invocations that do not format Markdown.
- Fixed
  - No longer mutate cached TOML options or `_conf.DEFAULT_OPTS`.
    This should avoid some hard to debug issues in plugins' tests.
- Added
  - `cache_toml` keyword argument to `_cli.run` for disabling TOML caching.
    This is useful in tests written for plugins.

## 0.7.21

- Fixed
  - Circular import in plugins that import from `mdformat.renderer`.

## 0.7.20

**NOTE:** This release was yanked from PyPI.

- Deprecated
  - `mdformat.codepoints.ASCII_WHITESPACE`.
    CommonMark no longer defines this since v0.30.
- Added
  - `--no-validate` flag for disabling the AST safety check.
    Thank you, [Kyle King](https://github.com/KyleKing), for the PR.
  - Added the delete control character to `mdformat.codepoints.ASCII_CTRL` as per CommonMark v0.30
- Fixed
  - The AST safety check not triggering when a code formatter plugin is in use,
    two or more code blocks are in the same file,
    and unsafe formatting happens in between the code blocks.

## 0.7.19

- Deprecated
  - Plugin interface: `mdformat.plugins.ParserExtensionInterface.add_cli_options`.
    The replacing interface is `mdformat.plugins.ParserExtensionInterface.add_cli_argument_group`.
- Fixed
  - Incorrect line wrap on lines right after a hard break.
    Thank you, [MDW](https://github.com/mdeweerd), for the issue.
  - Adding an extra leading space to paragraphs that start with space in line wrap modes.
  - An error on empty paragraph (Unicode space only) surrounded by non-paragraph elements.
    Thank you, [Nico Schlömer](https://github.com/nschloe), for the issue.
- Added
  - Plugin interface: `mdformat.plugins.ParserExtensionInterface.add_cli_argument_group`.
    With this plugins can now read CLI arguments merged with values from `.mdformat.toml`.
  - Option to select enabled (and required) extensions and code formatter languages
    (`--extensions` and `--codeformatters` on the CLI,
    and `extensions` and `codeformatters` keys in TOML).
  - Improved plugin list at the end of `--help` output:
    List languages supported by codeformatter plugin distributions,
    and parser extensions added by parser extension distributions.
- Changed
  - Style: No longer escape square bracket enclosures.
  - Style: No longer escape less than sign followed by space character.
  - Style: Convert tabs to spaces. Reduce space sequences to one space.
- Improved
  - Plugin interface: A trailing newline is added to fenced code blocks if a plugin fails to add it.

## 0.7.18

- Added
  - Option to exclude file paths using Unix-style glob patterns
    (`--exclude` on the CLI and `exclude` key in TOML).
    This feature is Python 3.13+ only.
    Thank you, [J. Sebastian Paez](https://github.com/jspaezp), for the issue.
- Removed
  - Python 3.8 support

## 0.7.17

- Added
  - Do not update mtime if formatting result is identical to the file.
    Thank you, [Pierre Augier](https://github.com/paugier), for the issue and the PR.
- Fixed
  - An error on empty paragraph (Unicode space only).
    Thank you, [Nico Schlömer](https://github.com/nschloe), for the issue.
  - File write fails if no permissions to write to the directory.
    Fixed by removing atomic writes.
    Thank you, [Guy Kisel](https://github.com/guykisel), for the issue.
  - File permissions change on rewrite.
    Thank you, [Keiichi Watanabe](https://github.com/keiichiw), for the issue.
- Removed
  - Python 3.7 support

## 0.7.16

- Added
  - Option to keep line ending sequence from source file (`--end-of-line=keep`).
    Thank you, [Mark Tsuchida](https://github.com/marktsuchida), for the issue and
    [Jan Wille](https://github.com/Cube707) for the PR.
- Fixed
  - `--check` not working with `--end-of-line=crlf`.
    Thank you, [Jan Wille](https://github.com/Cube707), for the issue.
  - Insignificant Unicode whitespace causing unstable formatting.
    Thank you, [Yamada_Ika](https://github.com/Yamada-Ika), for the issue.

## 0.7.15

- Fixed
  - `--wrap` converts Unicode whitespace to regular spaces and line feeds.
    Thank you, [Nico Schlömer](https://github.com/nschloe), for the issue.
- Packaging
  - Use `setuptools` as build backend

## 0.7.14

- Added
  - Accept `os.PathLike[str]` as `mdformat.file` input.
- Improved
  - Add filepath to warning message on code formatter plugin error.
  - Use `tomllib` in Python 3.11+.
- Changed
  - Style: Sort numeric link references numerically.
    Thank you [Ryan Delaney](https://github.com/rpdelaney) for the PR.

## 0.7.13

- Fixed
  - Don't indent inline HTML that looks like type 7 block HTML.
    Thank you [Philip May](https://github.com/PhilipMay) for the issue.

## 0.7.12

- Fixed
  - Fix unstable formatting when a paragraph line starts with inline HTML.
    Thank you [Gabriel Nützi](https://github.com/gabyx) for the issue.

## 0.7.11

- Added
  - Support for `markdown-it-py` v2
- Fixed
  - Fix an error when a code fence info string starts with a tilde or a backtick.
    Thank you [Jonathan Newnham](https://github.com/jnnnnn) for the issue.

## 0.7.10

- Added
  - Support for configuration in a `.mdformat.toml` file
- Removed
  - Python 3.6 support

## 0.7.9

- Fixed
  - Fix an error when an autolink contains URL encoded spaces.
    Thank you [Chris Butler](https://github.com/butler54) for the issue.

## 0.7.8

- Fixed
  - Fix a case where indented Markdown nested inside indented raw HTML tags would alter AST.
    Thank you [Jirka Borovec](https://github.com/Borda) for the issue.

## 0.7.7

- Fixed
  - Output `lf` line endings on all platforms.
    Thank you [Scott Gudeman](https://github.com/DragonCrafted87) for the issue and the PR.
- Added
  - Configuration option for outputting `crlf` line endings: `--end-of-line=crlf`
  - Resolve symlinks and modify the link destination file only.

## 0.7.6

- Changed
  - Style: Reduce wrap width by indent size in lists and quotes

## 0.7.5

- Fixed
  - Error rendering a hard break in a heading
  - Some obscure leading/trailing whitespace issues
  - Style: Convert image description newlines to spaces in wrap altering modes

## 0.7.4

- Added
  - `mdformat.renderer.WRAP_POINT` for plugins to show where word wrap is allowed to occur.
  - `mdformat.renderer.RenderContext.do_wrap` for plugins to check whether word wrap is enabled.
- Changed
  - Style: Emphasis and strong emphasis are now wrapped.
  - Style: Word wrap width target is now respected more precisely in a few edge cases.

## 0.7.3

- Fixed
  - Style: Convert link text newlines to spaces in wrap altering modes.
- Changed
  - Style: No longer escape line starting hashes not followed by a space.

## 0.7.2

- Fixed
  - Style: Stop adding a newline character to empty documents.

## 0.7.1

- Added
  - `RenderContext.with_default_renderer_for`:
    A convenience method for copying a render context with a set of renderers set to defaults

## 0.7.0

**NOTE:** Parser extension plugin API has changed in this release.

- Added
  - `POSTPROCESSORS` mapping to parser extension plugin API (i.e. `ParserExtensionInterface`),
    providing a way for plugins to render syntax collaboratively.
  - `Postprocess` type alias to `mdformat.renderer.typing`
  - `mdformat.renderer.RenderContext`: a context object passed as input to `Render` and `Postprocess` functions
- Changed
  - Renamed `ParserExtensionInterface.RENDERER_FUNCS` as `ParserExtensionInterface.RENDERERS`
  - Renamed `mdformat.renderer.typing.RendererFunc` as `mdformat.renderer.typing.Render`
  - `mdformat.renderer.typing.Render` signature changed. Now takes `RenderContext` as input.
  - Renamed `mdformat.renderer.DEFAULT_RENDERER_FUNCS` as `mdformat.renderer.DEFAULT_RENDERERS`

## 0.6.4

- Fixed
  - Warnings being printed twice when wrap mode is other than "keep"
    ([#167](https://github.com/hukkin/mdformat/pull/167))
  - An extra newline being added when consecutive lines' width equals wrap width
    ([#166](https://github.com/hukkin/mdformat/pull/166))

## 0.6.3

- Added
  - A list of installed plugins and their versions in the output of `--help` and `--version` CLI commands
  - `mdformat.codepoints` as public API

## 0.6.2

- Added
  - Sphinx docs
  - Atomic file writes.
    Markdown content now stays on disk every nanosecond of the formatting process.

## 0.6.1

- Fixed
  - A line starting blockquote marker (">") is now escaped.

## 0.6.0

**NOTE:** Parser extension plugin API has changed in this release.

- Removed
  - `mdformat.renderer.MARKERS`
  - `mdformat.plugins.ParserExtensionInterface.render_token`
  - `start` and `stop` keyword arguments removed from `mdformat.renderer.MDRenderer.render`.
    Use `mdformat.renderer.MDRenderer.render_tree` to render a part of a Markdown document.
- Added
  - Modes for setting a word wrap width and removing word wrap
  - `mdformat.plugins.ParserExtensionInterface.RENDERER_FUNCS`
  - A class for representing linear `markdown-it` token stream as a tree: `mdformat.renderer.RenderTreeNode`
  - `mdformat.renderer.MDRenderer.render_tree` for rendering a `RenderTreeNode`

## 0.5.7

- Fixed
  - CLI crash when formatting standard error output and the operating system reports a terminal window width of zero or less
    ([#131](https://github.com/hukkin/mdformat/issues/131)).
    Thank you [ehontoria](https://github.com/ehontoria) for the issue.

## 0.5.6

- Changed
  - Style: Reduce asterisk escaping
    ([#120](https://github.com/hukkin/mdformat/issues/120))
  - Style: Reduce underscore escaping
    ([#119](https://github.com/hukkin/mdformat/issues/119)).
    Thank you [dustinmichels](https://github.com/dustinmichels) for the issue.

## 0.5.5

- Changed
  - Style: Don't convert shortcut reference links into full reference links
    ([#111](https://github.com/hukkin/mdformat/issues/111))

## 0.5.4

- Changed
  - Style: Reduce hash (`#`) escaping

## 0.5.0

- Changed
  - Style: Convert list marker types.
    Prefer "-" for bullet lists and "." for ordered lists.
  - Style: Remove trailing whitespace from empty list items.

## 0.4.0

- Changed
  - Style: Only surround link destination with angle brackets if required by CommonMark spec
  - Style: Thematic breaks are now 70 characters wide

## 0.3.5

- Fixed
  - Markdown equality validation falsely triggering when code formatter plugins were used.
    Thanks [chrisjsewell](https://github.com/chrisjsewell) for writing the tests to find the bug.

## 0.3.3

- Added
  - `CHANGES_AST` to extension plugin API.
    The feature allows plugins that alter Markdown AST to skip validation
    ([#49](https://github.com/hukkin/mdformat/pull/49)).

## 0.3.2

- Changed
  - Style: Keep reference links as reference links ([#32](https://github.com/hukkin/mdformat/issues/32)).
    Thank you [chrisjsewell](https://github.com/chrisjsewell) for the issue and the PR.
- Added
  - Option to number ordered list items consecutively using the `--number` flag ([#33](https://github.com/hukkin/mdformat/issues/33)).
    Thank you [chrisjsewell](https://github.com/chrisjsewell) for the issue and the PR.
  - Parser extension plugins can now add their own CLI / Python API options ([#35](https://github.com/hukkin/mdformat/pull/35)).
    Thanks [chrisjsewell](https://github.com/chrisjsewell) for the PR.
- Fixed
  - Image links that require surrounding angle brackets no longer break formatting ([#40](https://github.com/hukkin/mdformat/issues/40)).

## 0.3.1

- Added
  - Plugin system for extending the parser ([#13](https://github.com/hukkin/mdformat/issues/13)).
    Thank you [chrisjsewell](https://github.com/chrisjsewell) for the issue and the PR.
  - Exported `mdformat.renderer.MDRenderer` and `mdformat.renderer.MARKERS`

## 0.3.0

- Changed
  - Code formatter plugin function signature changed to `Callable[[str, str], str]`.
    The second input argument is full info string of the code block.

## 0.2.0

- Changed
  - Style: Use backtick for code fences whenever possible

## 0.1.2

- Added
  - Support for code formatter plugins

## 0.1.0

- Added
  - Initial mdformat release
