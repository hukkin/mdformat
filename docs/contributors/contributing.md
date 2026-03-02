# Contributing

Welcome to the mdformat developer docs!
We're excited you're here and want to contribute. ✨

Please discuss new features in an issue before submitting a PR
to make sure that the feature is wanted and will be merged.
Note that mdformat is an opinionated tool
that attempts to keep formatting style changing configuration to its minimum.
New configuration will only be added for a very good reason and use case.

Below are the basic development steps.

1. Fork and clone the repository.

1. Install pre-commit hooks

   ```bash
   pre-commit install
   ```

1. After making changes and having written tests, make sure tests pass:

   ```bash
   tox
   ```

1. Test the pre-commit hook against the README.md file

   ```bash
   pre-commit try-repo . mdformat --files README.md
   ```

1. Commit, push, and make a PR.

## Developing code formatter plugins

Mdformat code formatter plugins need to define a formatter function that is of type `Callable[[str, str], str]`.
The input arguments are the code block's unformatted code and info string, in that order.
The return value should be formatted code.

This function needs to be exposed via entry point distribution metadata.
The entry point's group must be "mdformat.codeformatter",
name must be name of the coding language it formats (as it appears in Markdown code block info strings), e.g. "python",
and value has to point to the formatter function within the plugin package,
e.g. "my_package.some_module:format_python"

If using `setup.py` for packaging, the entry point configuration would have to be similar to:

```python
import setuptools

setuptools.setup(
    # other arguments here...
    entry_points={
        "mdformat.codeformatter": ["python = my_package.some_module:format_python"]
    }
)
```

If using a PEP 621 compliant build backend (e.g. Flit) for packaging, the entry point configuration in `pyproject.toml` would need to be like:

```toml
# other config here...
[project.entry-points."mdformat.codeformatter"]
"python" = "my_package.some_module:format_python"
```

For a real-world example plugin, see [mdformat-black](https://github.com/hukkin/mdformat-black),
which formats Python code blocks with Black.

## Developing parser extension plugins

The building blocks of an mdformat parses extension are typically:

- Extend mdformat's CommonMark parser to parse the syntax extension.
  Mdformat uses [markdown-it-py](https://github.com/executablebooks/markdown-it-py) to parse.
  Note that markdown-it-py offers a range of extensions to the base CommonMark parser (see the [documented list](https://markdown-it-py.readthedocs.io/en/latest/plugins.html)),
  so there's a chance the extension already exists.
- Activate the parser extension in mdformat.
- Add rendering support for the new syntax.
- Backslash escape the new syntax where applicable (typically either `text`, `inline` or `paragraph` renderers),
  to ensure mdformat doesn't render it when it must not.
  This could happen, for instance, when the syntax was backslash escaped in source Markdown.

The easiest way to get started on a plugin, is to use the <https://github.com/executablebooks/mdformat-plugin> template repository.

Mdformat parser extension plugins need to adhere to the `mdformat.plugins.ParserExtensionInterface`:

```python
from collections.abc import Mapping
from markdown_it import MarkdownIt
from mdformat.renderer.typing import Render


def update_mdit(mdit: MarkdownIt) -> None:
    """Update the parser, e.g. by adding a plugin: `mdit.use(myplugin)`"""


# A mapping from `RenderTreeNode.type` value to a `Render` function that can
# render the given `RenderTreeNode` type. These functions override the default
# `Render` funcs defined in `mdformat.renderer.DEFAULT_RENDERERS`.
RENDERERS: Mapping[str, Render]
```

This interface needs to be exposed via entry point distribution metadata.
The entry point's group must be "mdformat.parser_extension".

If using `setup.py` for packaging, the entry point configuration would have to be similar to:

```python
import setuptools

setuptools.setup(
    # other arguments here...
    entry_points={
        "mdformat.parser_extension": ["myextension = my_package:ext_module_or_class"]
    }
)
```

If using Poetry or Flit for packaging, the entry point configuration in `pyproject.toml` would need to be like:

```toml
# Poetry specific:
[tool.poetry.plugins."mdformat.parser_extension"]
"myextension" = "my_package:ext_module_or_class"
```

```toml
# or PEP 621 compliant (works with Flit):
[project.entry-points."mdformat.parser_extension"]
"myextension" = "my_package:ext_module_or_class"
```

## Making your plugin discoverable

In case you host your plugin on GitHub, make sure to add it under the "mdformat" topic so it shows up on <https://github.com/topics/mdformat>.
