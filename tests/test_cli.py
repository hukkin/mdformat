import io
import os
import sys
from unittest.mock import patch

import pytest

import mdformat
from mdformat._cli import get_plugin_info_str, run, wrap_paragraphs
from mdformat.plugins import CODEFORMATTERS, PARSER_EXTENSIONS
from tests.utils import (
    FORMATTED_MARKDOWN,
    UNFORMATTED_MARKDOWN,
    ASTChangingPlugin,
    PrefixPostprocessPlugin,
)


def test_no_files_passed():
    assert run(()) == 0


def test_format(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == FORMATTED_MARKDOWN


def test_format__folder(tmp_path):
    file_path_1 = tmp_path / "test_markdown1.md"
    file_path_2 = tmp_path / "test_markdown2.md"
    file_path_3 = tmp_path / "not_markdown3"
    file_path_1.write_text(UNFORMATTED_MARKDOWN)
    file_path_2.write_text(UNFORMATTED_MARKDOWN)
    file_path_3.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(tmp_path),)) == 0
    assert file_path_1.read_text() == FORMATTED_MARKDOWN
    assert file_path_2.read_text() == FORMATTED_MARKDOWN
    assert file_path_3.read_text() == UNFORMATTED_MARKDOWN


def test_format__folder_leads_to_invalid(tmp_path):
    file_path_1 = tmp_path / "test_markdown1.md"
    file_path_1.mkdir()
    assert run((str(tmp_path),)) == 0
    assert file_path_1.is_dir()


def test_format__symlinks(tmp_path):
    # Create two MD files
    file_path_1 = tmp_path / "test_markdown1.md"
    file_path_2 = tmp_path / "test_markdown2.md"
    file_path_1.write_text(UNFORMATTED_MARKDOWN)
    file_path_2.write_text(UNFORMATTED_MARKDOWN)

    # Create a symlink to both files: one in the root folder, one in a sub folder
    subdir_path = tmp_path / "subdir"
    subdir_path.mkdir()
    symlink_1 = subdir_path / "symlink1.md"
    symlink_1.symlink_to(file_path_1)
    symlink_2 = tmp_path / "symlink2.md"
    symlink_2.symlink_to(file_path_2)

    # Format file 1 via directory of the symlink, and file 2 via symlink
    assert run([str(subdir_path), str(symlink_2)]) == 0

    # Assert that files are formatted and symlinks are not overwritten
    assert file_path_1.read_text() == FORMATTED_MARKDOWN
    assert file_path_2.read_text() == FORMATTED_MARKDOWN
    assert symlink_1.is_symlink()
    assert symlink_2.is_symlink()


def test_broken_symlink(tmp_path, capsys):
    # Create a broken symlink
    file_path = tmp_path / "test_markdown1.md"
    symlink_path = tmp_path / "symlink"
    symlink_path.symlink_to(file_path)

    with pytest.raises(SystemExit) as exc_info:
        run([str(symlink_path)])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_invalid_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(("this is not a valid filepath?`=|><@{[]\\/,.%¤#'",))
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


@pytest.mark.skipif(os.name == "nt", reason="No os.mkfifo on windows")
def test_fifo(tmp_path, capsys):
    fifo_path = tmp_path / "fifo1"
    os.mkfifo(fifo_path)
    with pytest.raises(SystemExit) as exc_info:
        run((str(fifo_path),))
    assert exc_info.value.code == 2
    assert "does not exist" in capsys.readouterr().err


def test_check(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_bytes(FORMATTED_MARKDOWN.encode())
    assert run((str(file_path), "--check")) == 0


def test_check__fail(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(file_path), "--check")) == 1


def test_check__multi_fail(capsys, tmp_path):
    """Test for --check flag when multiple files are unformatted.

    Test that the names of all unformatted files are listed when using
    --check.
    """
    file_path1 = tmp_path / "test_markdown1.md"
    file_path2 = tmp_path / "test_markdown2.md"
    file_path1.write_text(UNFORMATTED_MARKDOWN)
    file_path2.write_text(UNFORMATTED_MARKDOWN)
    assert run((str(tmp_path), "--check")) == 1
    captured = capsys.readouterr()
    assert str(file_path1) in captured.err
    assert str(file_path2) in captured.err


def example_formatter(code, info):
    return "dummy\n"


def test_formatter_plugin(tmp_path, monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "lang", example_formatter)
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("```lang\nother\n```\n")
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "```lang\ndummy\n```\n"


def test_dash_stdin(capfd, patch_stdin):
    patch_stdin(UNFORMATTED_MARKDOWN)
    assert run(("-",)) == 0
    captured = capfd.readouterr()
    assert captured.out == FORMATTED_MARKDOWN


def test_wrap_paragraphs():
    with patch("shutil.get_terminal_size", return_value=(72, 24)):
        assert wrap_paragraphs(
            [
                'Error: Could not format "/home/user/file_name_longer_than_wrap_width--------------------------------------.md".',  # noqa: E501
                "The formatted Markdown renders to different HTML than the input Markdown. "  # noqa: E501
                "This is likely a bug in mdformat. "
                "Please create an issue report here: "
                "https://github.com/hukkin/mdformat/issues",
            ]
        ) == (
            "Error: Could not format\n"
            '"/home/user/file_name_longer_than_wrap_width--------------------------------------.md".\n'  # noqa: E501
            "\n"
            "The formatted Markdown renders to different HTML than the input\n"
            "Markdown. This is likely a bug in mdformat. Please create an issue\n"
            "report here: https://github.com/hukkin/mdformat/issues\n"
        )


def test_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith(f"mdformat {mdformat.__version__}")


def test_no_wrap(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(
        "all\n"
        "these newlines\n"
        "except the one in this hardbreak  \n"
        "should be\n"
        "removed because they are\n"
        "in the same paragraph\n"
        "\n"
        "This however is the next\n"
        "paragraph.    Whitespace should  be collapsed\n"
        "    \t here\n"
    )
    assert run([str(file_path), "--wrap=no"]) == 0
    assert (
        file_path.read_text()
        == "all these newlines except the one in this hardbreak\\\n"
        "should be removed because they are in the same paragraph\n"
        "\n"
        "This however is the next paragraph. Whitespace should be collapsed here\n"
    )


def test_wrap(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(
        "This\n"
        "text\n"
        "should\n"
        "be wrapped again so that wrap width is whatever is defined below. "
        "Also     whitespace            should\t\tbe             collapsed. "
        "Next up a second paragraph:\n"
        "\n"
        "This paragraph should also be wrapped. "
        "Here's some more text to wrap.  "
        "Here's some more text to wrap.  "
        "Here's some more text to wrap.  "
    )
    assert run([str(file_path), "--wrap=60"]) == 0
    assert (
        file_path.read_text()
        == "This text should be wrapped again so that wrap width is\n"
        "whatever is defined below. Also whitespace should be\n"
        "collapsed. Next up a second paragraph:\n"
        "\n"
        "This paragraph should also be wrapped. Here's some more text\n"
        "to wrap. Here's some more text to wrap. Here's some more\n"
        "text to wrap.\n"
    )


def test_consecutive_wrap_width_lines(tmp_path):
    """Test a case where two consecutive lines' width equals wrap width.

    There was a bug where this would cause an extra newline and split
    the paragraph, hence the test.
    """
    wrap_width = 20
    file_path = tmp_path / "test_markdown.md"
    text = "A" * wrap_width + "\n" + "A" * wrap_width + "\n"
    file_path.write_text(text)
    assert run([str(file_path), f"--wrap={wrap_width}"]) == 0
    assert file_path.read_text() == text


def test_wrap__hard_break(tmp_path):
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text(
        "This\n"
        "text\n"
        "should\n"
        "be wrapped again\\\n"
        "so that wrap width is whatever is defined below. "
        "Also     whitespace            should\t\tbe             collapsed."
    )
    assert run([str(file_path), "--wrap=60"]) == 0
    assert (
        file_path.read_text() == "This text should be wrapped again\\\n"
        "so that wrap width is whatever is defined below. Also\n"
        "whitespace should be collapsed.\n"
    )


def test_bad_wrap_width(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run(["some-path.md", "--wrap=-1"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "error: argument --wrap" in captured.err


def test_eol__lf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\r\n")
    assert run([str(file_path)]) == 0
    assert file_path.read_bytes() == b"Oi\n"


def test_eol__crlf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\n")
    assert run([str(file_path), "--end-of-line=crlf"]) == 0
    assert file_path.read_bytes() == b"Oi\r\n"


def test_eol__keep_lf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\n")
    assert run([str(file_path), "--end-of-line=keep"]) == 0
    assert file_path.read_bytes() == b"Oi\n"


def test_eol__keep_crlf(tmp_path):
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"Oi\r\n")
    assert run([str(file_path), "--end-of-line=keep"]) == 0
    assert file_path.read_bytes() == b"Oi\r\n"


def test_eol__crlf_stdin(capfd, patch_stdin):
    patch_stdin("Oi\n")
    assert run(["-", "--end-of-line=crlf"]) == 0
    captured = capfd.readouterr()
    assert captured.out == "Oi\r\n"


def test_eol__check_lf(tmp_path):
    file_path = tmp_path / "test.md"

    file_path.write_bytes(b"lol\r\n")
    assert run((str(file_path), "--check")) == 1

    file_path.write_bytes(b"lol\n")
    assert run((str(file_path), "--check")) == 0


def test_eol__check_crlf(tmp_path):
    file_path = tmp_path / "test.md"

    file_path.write_bytes(b"lol\n")
    assert run((str(file_path), "--check", "--end-of-line=crlf")) == 1

    file_path.write_bytes(b"lol\r\n")
    assert run((str(file_path), "--check", "--end-of-line=crlf")) == 0


def test_eol__check_keep_lf(tmp_path):
    file_path = tmp_path / "test.md"

    file_path.write_bytes(b"lol\n")
    assert run((str(file_path), "--check", "--end-of-line=keep")) == 0

    file_path.write_bytes(b"mixed\nEOLs\r")
    assert run((str(file_path), "--check", "--end-of-line=keep")) == 1


def test_eol__check_keep_crlf(tmp_path):
    file_path = tmp_path / "test.md"

    file_path.write_bytes(b"lol\r\n")
    assert run((str(file_path), "--check", "--end-of-line=keep")) == 0

    file_path.write_bytes(b"mixed\r\nEOLs\n")
    assert run((str(file_path), "--check", "--end-of-line=keep")) == 1


def test_cli_no_validate(tmp_path):
    file_path = tmp_path / "test.md"
    content = "1. ordered"
    file_path.write_text(content)

    with patch("mdformat.renderer._context.get_list_marker_type", return_value="?"):
        assert run((str(file_path),)) == 1
        assert file_path.read_text() == content

        assert run((str(file_path), "--no-validate")) == 0
        assert file_path.read_text() == "1? ordered\n"


def test_get_plugin_info_str():
    info = get_plugin_info_str(
        {"mdformat-tables": ("0.1.0", ["tables"])},
        {"mdformat-black": ("12.1.0", ["python"])},
    )
    assert (
        info
        == """\
installed codeformatters:
  mdformat-black: python

installed extensions:
  mdformat-tables: tables"""
    )


def test_no_timestamp_modify(tmp_path):
    file_path = tmp_path / "test.md"

    file_path.write_bytes(b"lol\n")
    initial_access_time = 0
    initial_mod_time = 0
    os.utime(file_path, (initial_access_time, initial_mod_time))

    # Assert that modification time does not change when no changes are applied
    assert run([str(file_path)]) == 0
    assert os.path.getmtime(file_path) == initial_mod_time


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="'exclude' only possible on 3.13+"
)
def test_exclude(tmp_path):
    subdir_path_1 = tmp_path / "folder1"
    subdir_path_2 = subdir_path_1 / "folder2"
    file_path_1 = subdir_path_2 / "file1.md"
    subdir_path_1.mkdir()
    subdir_path_2.mkdir()
    file_path_1.write_text(UNFORMATTED_MARKDOWN)
    cwd = tmp_path

    with patch("mdformat._cli.Path.cwd", return_value=cwd):
        for good_pattern in [
            "folder1/folder2/file1.md",
            "**",
            "**/*.md",
            "**/file1.md",
            "folder1/**",
        ]:
            assert run([str(file_path_1), "--exclude", good_pattern]) == 0
            assert file_path_1.read_text() == UNFORMATTED_MARKDOWN

        for bad_pattern in [
            "**file1.md",
            "file1.md",
            "folder1",
            "*.md",
            "*",
            "folder1/*",
        ]:
            file_path_1.write_text(UNFORMATTED_MARKDOWN)
            assert run([str(file_path_1), "--exclude", bad_pattern]) == 0
            assert file_path_1.read_text() == FORMATTED_MARKDOWN


def test_codeformatters(tmp_path, monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "enabled-lang", lambda code, info: "dumdum")
    monkeypatch.setitem(CODEFORMATTERS, "disabled-lang", lambda code, info: "dumdum")
    file_path = tmp_path / "test.md"
    unformatted = """\
```disabled-lang
hey
```

```enabled-lang
hey
```
"""
    formatted = """\
```disabled-lang
hey
```

```enabled-lang
dumdum
```
"""
    file_path.write_text(unformatted)
    assert run((str(file_path), "--codeformatters", "enabled-lang")) == 0
    assert file_path.read_text() == formatted


def test_extensions(tmp_path, monkeypatch):
    ast_plugin_name = "ast-plug"
    prefix_plugin_name = "prefix-plug"
    monkeypatch.setitem(PARSER_EXTENSIONS, ast_plugin_name, ASTChangingPlugin)
    monkeypatch.setitem(PARSER_EXTENSIONS, prefix_plugin_name, PrefixPostprocessPlugin)
    unformatted = "original text\n"
    file_path = tmp_path / "test.md"

    file_path.write_text(unformatted)
    assert run((str(file_path), "--extensions", "prefix-plug")) == 0
    assert file_path.read_text() == "Prefixed!original text\n"

    file_path.write_text(unformatted)
    assert run((str(file_path), "--extensions", "ast-plug")) == 0
    assert file_path.read_text() == ASTChangingPlugin.TEXT_REPLACEMENT + "\n"

    file_path.write_text(unformatted)
    assert (
        run((str(file_path), "--extensions", "ast-plug", "--extensions", "prefix-plug"))
        == 0
    )
    assert (
        file_path.read_text() == "Prefixed!" + ASTChangingPlugin.TEXT_REPLACEMENT + "\n"
    )


def test_codeformatters__invalid(tmp_path, capsys):
    file_path = tmp_path / "test.md"
    file_path.write_text("")
    assert run((str(file_path), "--codeformatters", "no-exists")) == 1
    captured = capsys.readouterr()
    assert "Error: Invalid code formatter required" in captured.err


def test_extensions__invalid(tmp_path, capsys):
    file_path = tmp_path / "test.md"
    file_path.write_text("")
    assert run((str(file_path), "--extensions", "no-exists")) == 1
    captured = capsys.readouterr()
    assert "Error: Invalid extension required" in captured.err


def test_no_codeformatters(tmp_path, monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "lang", lambda code, info: "dumdum")
    file_path = tmp_path / "test.md"
    original_md = """\
```lang
original code
```
"""
    file_path.write_text(original_md)
    assert run((str(file_path), "--no-codeformatters")) == 0
    assert file_path.read_text() == original_md


def test_no_extensions(tmp_path, monkeypatch):
    plugin_name = "plug-name"
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name, ASTChangingPlugin)
    file_path = tmp_path / "test.md"
    original_md = "original md\n"
    file_path.write_text(original_md)
    assert run((str(file_path), "--no-extensions")) == 0
    assert file_path.read_text() == original_md


def test_config_override_precedence(tmp_path):
    explicit_config_path = tmp_path / "explicit.toml"
    explicit_config_path.write_text("wrap = 50\nend_of_line = 'crlf'")

    auto_config_path = tmp_path / ".mdformat.toml"
    auto_config_path.write_text("wrap = 100")

    file_path = tmp_path / "test.md"
    file_path.write_text(
        "A very long line to test wrapping and EOLs.\nA very very long line."
    )

expected_content = (
        "A very long line to test wrapping and EOLs. A very" + "\r\n"
        + "very long line." + "\r\n"
    )

    assert run([str(file_path), "--config", str(explicit_config_path)]) == 0
    assert file_path.read_bytes() == expected_content.encode("utf-8")

    non_existent_path = tmp_path / "non_existent.toml"
    unformatted_content = "unformatted content"
    file_path.write_text(unformatted_content)

    assert run([str(file_path), "--config", str(non_existent_path)]) == 1
    assert file_path.read_text() == unformatted_content


def test_config_search_from_stdin(tmp_path, capfd, patch_stdin):
    """Test that config is searched from CWD when reading from stdin (path is
    None)."""

    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("wrap = 50")

    input_content = "This is a very long line that should be wrapped if config is read."

    expected_content = """\
This is a very long line that should be wrapped if
config is read.
"""

    with patch("os.getcwd", return_value=str(tmp_path)):
        patch_stdin(input_content)

        assert run(("-",)) == 0

        captured = capfd.readouterr()

        assert captured.out == expected_content