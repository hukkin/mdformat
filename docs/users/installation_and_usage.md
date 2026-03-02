# Installation and usage

```{include} ../../README.md
:start-after: <!-- start installing -->
:end-before: <!-- end installing -->
```

```{warning}
The formatting style produced by mdformat may change in each version.
It is recommended to pin mdformat dependency version.
```

```{include} ../../README.md
:start-after: <!-- start cli-usage -->
:end-before: <!-- end cli-usage -->
```

## Python API usage

### Format text

```python
import mdformat

unformatted = "\n\n# A header\n\n"
formatted = mdformat.text(unformatted)
assert formatted == "# A header\n"
```

### Format a file

Format file `README.md` in place:

```python
import mdformat

# Input filepath as a string...
mdformat.file("README.md")

# ...or a pathlib.Path object
import pathlib

filepath = pathlib.Path("README.md")
mdformat.file(filepath)
```

### Options

All formatting style modifying options available in the CLI are also available in the Python API,
with equivalent option names:

```python
import mdformat

mdformat.file(
    "FILENAME.md",
    options={
        "number": True,  # switch on consecutive numbering of ordered lists
        "wrap": 60,  # set word wrap width to 60 characters
    }
)
```

## Usage as a pre-commit hook

`mdformat` can be used as a [pre-commit](https://github.com/pre-commit/pre-commit) hook.
Add the following to your project's `.pre-commit-config.yaml` to enable this:

```yaml
- repo: https://github.com/hukkin/mdformat
  rev: 1.0.0  # Use the ref you want to point at
  hooks:
  - id: mdformat
    # Optionally add plugins
    additional_dependencies:
    - mdformat-gfm
    - mdformat-black
```
