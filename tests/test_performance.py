import subprocess
import sys

import pytest


def test_importtime__no_mdit_import():
    """Test that `markdown_it` isn't imported when `mdformat` and
    `mdformat._cli` are.

    Do this in a subprocess to have a clean environment separate from
    pytest and other tests.
    """
    test_script = """\
import sys
import mdformat
import mdformat._cli
assert 'markdown_it' not in sys.modules, 'markdown_it was imported'
"""
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        stdin=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        assert (
            b"markdown_it was imported" in result.stderr
        ), "unexpected error in subprocess"
        pytest.fail("markdown_it was imported")
