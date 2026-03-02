"""Test for profiling.

This test can be useful for profiling, as most of the execution time
will be spent parsing and rendering instead of managing pytest execution
environment. The test simply ensures that the README and Markdown docs
in this project are formatted. To get and read profiler results:
  - `tox -e profile`
  - `firefox .tox/prof/combined.svg`
"""

from pathlib import Path

from mdformat._cli import run

PROJECT_ROOT = Path(__file__).parent.parent
# Make a few asserts to ensure this actually is the project root
# (a safeguard against refactorings where this file is moved).
assert (PROJECT_ROOT / "docs").exists()
assert (PROJECT_ROOT / "README.md").exists()
assert (PROJECT_ROOT / "src" / "mdformat").exists()


def test_for_profiler():
    docs_path = PROJECT_ROOT / "docs"
    readme_path = PROJECT_ROOT / "README.md"
    assert run([str(docs_path), str(readme_path), "--check"]) == 0
    # Also profile --wrap=INT code
    run([str(docs_path), str(readme_path), "--check", "--wrap", "50"])
