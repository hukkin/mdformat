import sys
from unittest import mock

import pytest

from mdformat._cli import run
from tests.utils import FORMATTED_MARKDOWN, UNFORMATTED_MARKDOWN


def test_cli_override(tmp_path):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("wrap = 'no'\nend_of_line = 'lf'")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("remove\nthis\nwrap\n")

    assert run((str(file_path), "--wrap=keep")) == 0
    assert file_path.read_text() == "remove\nthis\nwrap\n"

    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "remove this wrap\n"


def test_conf_in_parent_dir(tmp_path):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("wrap = 'no'")

    subdir_path = tmp_path / "subdir"
    subdir_path.mkdir()
    file_path = subdir_path / "test_markdown.md"
    file_path.write_text("remove\nthis\nwrap")

    assert run((str(file_path),)) == 0
    assert file_path.read_text() == "remove this wrap\n"


def test_invalid_conf_key(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("numberr = true")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("1. one\n1. two\n1. three")

    assert run((str(file_path),)) == 1
    captured = capsys.readouterr()
    assert "Invalid key 'numberr'" in captured.err


def test_invalid_toml(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("]invalid TOML[")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("some markdown\n")

    assert run((str(file_path),)) == 1
    captured = capsys.readouterr()
    assert "Invalid TOML syntax" in captured.err


@pytest.mark.parametrize(
    "conf_key, bad_conf",
    [
        ("wrap", "wrap = -3"),
        ("end_of_line", "end_of_line = 'lol'"),
        ("validate", "validate = 'off'"),
        ("number", "number = 0"),
        ("exclude", "exclude = '**'"),
        ("exclude", "exclude = ['1',3]"),
        ("plugin", "plugin = []"),
        ("plugin", "plugin.gfm = {}\nplugin.myst = 1"),
        ("codeformatters", "codeformatters = 'python'"),
        ("extensions", "extensions = 'gfm'"),
        ("codeformatters", "codeformatters = ['python', 1]"),
        ("extensions", "extensions = ['gfm', 1]"),
    ],
)
def test_invalid_conf_value(bad_conf, conf_key, tmp_path, capsys):
    if conf_key == "exclude" and sys.version_info < (3, 13):
        pytest.skip("exclude conf only on Python 3.13+")
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text(bad_conf)

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("# Test Markdown")

    assert run((str(file_path),)) == 1
    captured = capsys.readouterr()
    assert f"Invalid '{conf_key}' value" in captured.err


def test_conf_with_stdin(tmp_path, capfd, patch_stdin):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("number = true")

    patch_stdin("1. one\n1. two\n1. three")

    with mock.patch("mdformat._cli.Path.cwd", return_value=tmp_path):
        assert run(("-",), cache_toml=False) == 0
    captured = capfd.readouterr()
    assert captured.out == "1. one\n2. two\n3. three\n"


@pytest.mark.skipif(
    sys.version_info >= (3, 13), reason="'exclude' only possible on 3.13+"
)
def test_exclude_conf_on_old_python(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("exclude = ['**']")

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("# Test Markdown")

    assert run((str(file_path),)) == 1
    assert "only available on Python 3.13+" in capsys.readouterr().err


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="'exclude' only possible on 3.13+"
)
def test_exclude(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("exclude = ['dir1/*', 'file1.md']")

    dir1_path = tmp_path / "dir1"
    file1_path = tmp_path / "file1.md"
    file2_path = tmp_path / "file2.md"
    file3_path = tmp_path / dir1_path / "file3.md"
    dir1_path.mkdir()
    file1_path.write_text(UNFORMATTED_MARKDOWN)
    file2_path.write_text(UNFORMATTED_MARKDOWN)
    file3_path.write_text(UNFORMATTED_MARKDOWN)

    assert run((str(tmp_path),)) == 0
    assert file1_path.read_text() == UNFORMATTED_MARKDOWN
    assert file2_path.read_text() == FORMATTED_MARKDOWN
    assert file3_path.read_text() == UNFORMATTED_MARKDOWN


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="'exclude' only possible on 3.13+"
)
def test_empty_exclude(tmp_path, capsys):
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("exclude = []")

    file1_path = tmp_path / "file1.md"
    file1_path.write_text(UNFORMATTED_MARKDOWN)

    assert run((str(tmp_path),)) == 0
    assert file1_path.read_text() == FORMATTED_MARKDOWN


def test_conf_no_validate(tmp_path):
    file_path = tmp_path / "file.md"
    content = "1. ordered"
    file_path.write_text(content)

    with mock.patch(
        "mdformat.renderer._context.get_list_marker_type",
        return_value="?",
    ):
        assert run((str(file_path),), cache_toml=False) == 1
        assert file_path.read_text() == content

        config_path = tmp_path / ".mdformat.toml"
        config_path.write_text("validate = false")

        assert run((str(file_path),), cache_toml=False) == 0
        assert file_path.read_text() == "1? ordered\n"


def test_single_config_file_invalid_toml(tmp_path):
    """Test that reading an explicitly supplied config file with invalid TOML
    raises InvalidConfError."""
    invalid_toml_path = tmp_path / "invalid.toml"
    invalid_toml_path.write_text("key = 'value\n[broken")

    with pytest.raises(InvalidConfError) as excinfo:
        read_single_config_file(invalid_toml_path)

    assert f"Invalid TOML syntax in {invalid_toml_path}" in str(excinfo.value)
