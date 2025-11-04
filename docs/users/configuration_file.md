# Configuration file

Mdformat allows configuration in a [TOML](https://toml.io) file named `.mdformat.toml`.

The configuration file will be resolved starting from the location of the file being formatted,
and searching up the file tree until a config file is (or isn't) found.
When formatting standard input stream, resolution will be started from current working directory.

Command line interface arguments take precedence over the configuration file.

### Explicit Configuration Path

Alternatively, you can explicitly point to a configuration file using the **`--config`** command-line argument. When this argument is used, the default recursive search for `.mdformat.toml` is **disabled**, and only the configuration found at the specified path will be loaded. This provides direct control over the configuration file location, which is useful when integrating `mdformat` into tools like `pre-commit` hooks that require configs to be stored in custom locations.

**Example:**

```bash
mdformat file.md --config .config/mdformat.toml
```

## Example configuration

```toml
# .mdformat.toml
#
# This file shows the default values and is equivalent to having
# no configuration file at all. Change the values for non-default
# behavior.
#
wrap = "keep"         # options: {"keep", "no", INTEGER}
number = false        # options: {false, true}
end_of_line = "lf"    # options: {"lf", "crlf", "keep"}
validate = true       # options: {false, true}
# extensions = [      # options: a list of enabled extensions (default: all installed are enabled)
#     "gfm",
#     "toc",
# ]
# codeformatters = [  # options: a list of enabled code formatter languages (default: all installed are enabled)
#     "python",
#     "json",
# ]

# Python 3.13+ only:
exclude = []          # options: a list of file path pattern strings
```

## Exclude patterns

A list of file exclusion patterns can be defined on Python 3.13+.
Unix-style glob patterns are supported, see
[Python's documentation](https://docs.python.org/3/library/pathlib.html#pattern-language)
for syntax definition.

Glob patterns are matched against relative paths.
If `--exclude` is used on the command line, the paths are relative to current working directory.
Else the paths are relative to the parent directory of the file's `.mdformat.toml`.

Only files (recursively) contained by the base directory can be excluded.

Files that match an exclusion pattern are _always_ excluded,
even in the case that they are directly referenced in a command line invocation.

### Example patterns

```toml
# .mdformat.toml
exclude = [
    # exclude a single root level file
    "CHANGELOG.md",

    # recursively exclude a root level directory
    "venv/**",

    # recursively exclude a directory at any level
    "**/node_modules/**",

    # exclude all .txt files
    "**/*.txt",

    # exclude all files that are not suffixed .md
    "**/?", "**/??", "**/???", "**/*[!.]??", "**/*[!m]?", "**/*[!d]",
]
```
