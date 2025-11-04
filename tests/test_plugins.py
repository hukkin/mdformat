import argparse
import importlib.metadata
import inspect
from textwrap import dedent
from unittest.mock import patch

from markdown_it import MarkdownIt
import pytest

import mdformat
from mdformat._cli import run
from mdformat.plugins import (
    _PARSER_EXTENSION_DISTS,
    CODEFORMATTERS,
    PARSER_EXTENSIONS,
    _load_entrypoints,
)
from mdformat.renderer import MDRenderer
from tests.utils import (
    ASTChangingPlugin,
    JSONFormatterPlugin,
    PrefixPostprocessPlugin,
    SuffixPostprocessPlugin,
    TablePlugin,
    TextEditorPlugin,
)


def test_code_formatter(monkeypatch):
    def fmt_func(code, info):
        return "dummy\n"

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ```lang
    a
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    dummy
    ```
    """
    )


def test_code_formatter__empty_str(monkeypatch):
    def fmt_func(code, info):
        return ""

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ~~~lang
    aag
    gw
    ~~~
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    ```
    """
    )


def test_code_formatter__no_end_newline(monkeypatch):
    def fmt_func(code, info):
        return "dummy\ndum"

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ```lang
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang
    dummy
    dum
    ```
    """
    )


def test_code_formatter__interface(monkeypatch):
    def fmt_func(code, info):
        return info + code * 2

    monkeypatch.setitem(CODEFORMATTERS, "lang", fmt_func)
    text = mdformat.text(
        dedent(
            """\
    ```    lang  long
    multi
    mul
    ```
    """
        ),
        codeformatters={"lang"},
    )
    assert text == dedent(
        """\
    ```lang  long
    lang  longmulti
    mul
    multi
    mul
    ```
    """
    )


def test_single_token_extension(monkeypatch):
    """Test the front matter plugin, as a single token extension example."""
    plugin_name = "text_editor"
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name, TextEditorPlugin)
    text = mdformat.text(
        dedent(
            """\
    # Example Heading

    Example paragraph.
    """
        ),
        extensions=[plugin_name],
    )
    assert text == dedent(
        """\
    # All text is like this now!

    All text is like this now!
    """
    )


def test_table(monkeypatch):
    """Test the table plugin, as a multi-token extension example."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", TablePlugin)
    text = mdformat.text(
        dedent(
            """\
    |a|b|
    |-|-|
    |c|d|

    other text
    """
        ),
        extensions=["table", "table"],
    )
    assert text == dedent(
        """\
    dummy 21

    other text
    """
    )


class ExamplePluginWithGroupedCli:
    """A plugin that adds CLI options."""

    @staticmethod
    def update_mdit(mdit: MarkdownIt):
        mdit.enable("table")

    @staticmethod
    def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
        group.add_argument("--o1", type=str)
        group.add_argument("--o2", type=str, default="a")
        group.add_argument("--o3", dest="arg_name", type=int)
        group.add_argument("--override-toml")
        group.add_argument("--dont-override-toml", action="store_const", const=True)


def test_cli_options_group(monkeypatch, tmp_path):
    """Test that CLI arguments added by plugins are correctly added to the
    options dict.

    Use add_cli_argument_group plugin API.
    """
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithGroupedCli)
    file_path = tmp_path / "test_markdown.md"
    conf_path = tmp_path / ".mdformat.toml"
    file_path.touch()
    conf_path.write_text(
        """\
[plugin.table]
override_toml = 'failed'
toml_only = true
dont_override_toml = 'dont override this with None if CLI opt not given'
"""
    )

    with patch.object(MDRenderer, "render", return_value="") as mock_render:
        assert (
            run(
                (
                    str(file_path),
                    "--o1",
                    "other",
                    "--o3",
                    "4",
                    "--override-toml",
                    "success",
                )
            )
            == 0
        )

    (call_,) = mock_render.call_args_list
    posargs = call_[0]
    # Options is the second positional arg of MDRender.render
    opts = posargs[1]
    table_opts = opts["mdformat"]["plugin"]["table"]
    assert table_opts["o1"] == "other"
    assert table_opts["o2"] == "a"
    assert table_opts["arg_name"] == 4
    assert table_opts["override_toml"] == "success"
    assert table_opts["toml_only"] is True
    assert (
        table_opts["dont_override_toml"]
        == "dont override this with None if CLI opt not given"
    )


def test_plugin_argument_warnings(monkeypatch, tmp_path):
    """Test for warnings of plugin arguments that conflict with TOML."""

    class ExamplePluginWithStoreTrue:
        @staticmethod
        def update_mdit(mdit: MarkdownIt):
            pass

        @staticmethod
        def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
            group.add_argument("--store-true", action="store_true")
            group.add_argument("--store-false", action="store_false")
            group.add_argument("--store-zero", default=0)
            group.add_argument("--store-const", action="store_const", const=True)

    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithStoreTrue)
    file_path = tmp_path / "test_markdown.md"
    file_path.touch()

    with patch.object(MDRenderer, "render", return_value=""):
        with pytest.warns(DeprecationWarning) as warnings:
            assert run([str(file_path)]) == 0

    assert "--store-true" in str(warnings.pop().message)
    assert "--store-false" in str(warnings.pop().message)
    assert "--store-zero" in str(warnings.pop().message)
    assert len(warnings) == 0


def test_cli_options_group__no_toml(monkeypatch, tmp_path):
    """Test add_cli_argument_group plugin API with configuration only from
    CLI."""
    monkeypatch.setitem(PARSER_EXTENSIONS, "table", ExamplePluginWithGroupedCli)
    file_path = tmp_path / "test_markdown.md"
    file_path.touch()

    with patch.object(MDRenderer, "render", return_value="") as mock_render:
        assert run((str(file_path), "--o1", "other")) == 0

    (call_,) = mock_render.call_args_list
    posargs = call_[0]
    # Options is the second positional arg of MDRender.render
    opts = posargs[1]
    assert opts["mdformat"]["plugin"]["table"]["o1"] == "other"


def test_ast_changing_plugin(monkeypatch, tmp_path):
    plugin = ASTChangingPlugin()
    monkeypatch.setitem(PARSER_EXTENSIONS, "ast_changer", plugin)
    file_path = tmp_path / "test_markdown.md"

    # Test that the AST changing formatting is applied successfully
    # under normal operation.
    file_path.write_text("Some markdown here\n")
    assert run((str(file_path),)) == 0
    assert file_path.read_text() == plugin.TEXT_REPLACEMENT + "\n"

    # Set the plugin's `CHANGES_AST` flag to False and test that the
    # equality check triggers, notices the AST breaking changes and a
    # non-zero error code is returned.
    plugin.CHANGES_AST = False
    file_path.write_text("Some markdown here\n")
    assert run((str(file_path),)) == 1
    assert file_path.read_text() == "Some markdown here\n"


def test_code_format_warnings__cli(monkeypatch, tmp_path, capsys):
    monkeypatch.setitem(CODEFORMATTERS, "json", JSONFormatterPlugin.format_json)
    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("```json\nthis is invalid json\n```\n")
    assert run([str(file_path)]) == 0
    captured = capsys.readouterr()
    assert (
        captured.err
        == f"Warning: Failed formatting content of a json code block (line 1 before formatting). Filename: {file_path}\n"  # noqa: E501
    )


def test_code_format_warnings__api(monkeypatch, caplog):
    monkeypatch.setitem(CODEFORMATTERS, "json", JSONFormatterPlugin.format_json)
    assert (
        mdformat.text("```json\nthis is invalid json\n```\n", codeformatters=("json",))
        == "```json\nthis is invalid json\n```\n"
    )
    assert (
        caplog.messages[0]
        == "Failed formatting content of a json code block (line 1 before formatting)"
    )


def test_plugin_conflict(monkeypatch, tmp_path, capsys):
    """Test a warning when plugins try to render same syntax."""
    plugin_name_1 = "plug1"
    plugin_name_2 = "plug2"
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name_1, TextEditorPlugin)
    monkeypatch.setitem(PARSER_EXTENSIONS, plugin_name_2, ASTChangingPlugin)

    file_path = tmp_path / "test_markdown.md"
    file_path.write_text("some markdown here")
    assert run([str(file_path)]) == 0
    captured = capsys.readouterr()
    assert (
        captured.err
        == 'Warning: Plugin conflict. More than one plugin defined a renderer for "text" syntax.\n'  # noqa: E501
    )


def test_plugin_versions_in_cli_help(monkeypatch, capsys):
    monkeypatch.setitem(
        _PARSER_EXTENSION_DISTS, "table-dist", ("v3.2.1", ["table-ext"])
    )
    with pytest.raises(SystemExit) as exc_info:
        run(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "installed extensions:" in captured.out
    assert "table-dist: table-ext" in captured.out


def test_postprocess_plugins(monkeypatch):
    """Test that postprocessors work collaboratively."""
    suffix_plugin_name = "suffixer"
    prefix_plugin_name = "prefixer"
    monkeypatch.setitem(PARSER_EXTENSIONS, suffix_plugin_name, SuffixPostprocessPlugin)
    monkeypatch.setitem(PARSER_EXTENSIONS, prefix_plugin_name, PrefixPostprocessPlugin)
    text = mdformat.text(
        dedent(
            """\
            # Example Heading.

            Example paragraph.
            """
        ),
        extensions=[suffix_plugin_name, prefix_plugin_name],
    )
    assert text == dedent(
        """\
        # Prefixed!Example Heading.Suffixed!

        Prefixed!Example paragraph.Suffixed!
        """
    )


def test_load_entrypoints(tmp_path, monkeypatch):
    """Test the function that loads plugins to constants."""
    # Create a minimal .dist-info to create EntryPoints out of
    dist_info_path = tmp_path / "mdformat_gfm-0.3.6.dist-info"
    dist_info_path.mkdir()
    entry_points_path = dist_info_path / "entry_points.txt"
    metadata_path = dist_info_path / "METADATA"
    # The modules here will get loaded so use ones we know will always exist
    # (even though they aren't actual extensions).
    entry_points_path.write_text(
        """\
[mdformat.parser_extension]
ext1=mdformat.plugins
ext2=mdformat.plugins
"""
    )
    metadata_path.write_text(
        """\
Metadata-Version: 2.1
Name: mdformat-gfm
Version: 0.3.6
"""
    )
    distro = importlib.metadata.PathDistribution(dist_info_path)
    entrypoints = distro.entry_points

    loaded_eps, dist_infos = _load_entrypoints(entrypoints)
    assert loaded_eps == {"ext1": mdformat.plugins, "ext2": mdformat.plugins}
    assert dist_infos == {"mdformat-gfm": ("0.3.6", ["ext1", "ext2"])}


def test_no_codeformatters__toml(tmp_path, monkeypatch):
    monkeypatch.setitem(CODEFORMATTERS, "json", JSONFormatterPlugin.format_json)
    unformatted = """\
```json
{"a": "b"}
```
"""
    formatted = """\
```json
{
  "a": "b"
}
```
"""
    file1_path = tmp_path / "file1.md"

    # Without TOML
    file1_path.write_text(unformatted)
    assert run((str(tmp_path),)) == 0
    assert file1_path.read_text() == formatted

    # With TOML
    file1_path.write_text(unformatted)
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("codeformatters = []")
    assert run((str(tmp_path),), cache_toml=False) == 0
    assert file1_path.read_text() == unformatted


def test_no_extensions__toml(tmp_path, monkeypatch):
    plugin = ASTChangingPlugin()
    monkeypatch.setitem(PARSER_EXTENSIONS, "ast_changer", plugin)
    unformatted = "text\n"
    formatted = plugin.TEXT_REPLACEMENT + "\n"
    file1_path = tmp_path / "file1.md"

    # Without TOML
    file1_path.write_text(unformatted)
    assert run((str(tmp_path),)) == 0
    assert file1_path.read_text() == formatted

    # With TOML
    file1_path.write_text(unformatted)
    config_path = tmp_path / ".mdformat.toml"
    config_path.write_text("extensions = []")
    assert run((str(tmp_path),), cache_toml=False) == 0
    assert file1_path.read_text() == unformatted


class MockPluginWithDefault:
    @staticmethod
    def update_mdit(mdit):
        pass

    @staticmethod
    def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:

        group.add_argument("--test-arg", default="a")

    RENDERERS = {}


def test_cli_argument_default_warning(monkeypatch, caplog):
    """Checks that the internal code path for checking plugin argument defaults
    is covered."""
    from mdformat import plugins
    from mdformat._cli import make_arg_parser

    plugin_name = "test-warn-plugin"
    monkeypatch.setitem(plugins.PARSER_EXTENSIONS, plugin_name, MockPluginWithDefault)

    with monkeypatch.context() as m:
        m.setattr(
            plugins,
            "get_source_file_and_line",
            lambda obj: (inspect.getsourcefile(MockPluginWithDefault), 175),
        )

        parser = make_arg_parser(
            plugins._PARSER_EXTENSION_DISTS,
            plugins._CODEFORMATTER_DISTS,
            plugins.PARSER_EXTENSIONS,
        )

        cli_args = ["--test-warn-plugin.test-arg", "new-value", "dummy.md"]
        opts = parser.parse_args(cli_args)

        assert getattr(opts, f"plugin.{plugin_name}.test_arg") == "new-value"
