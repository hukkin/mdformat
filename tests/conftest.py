import io
import sys

import pytest


@pytest.fixture
def patch_stdin(monkeypatch):
    """Fixture to patch sys.stdin for the running test."""

    def set_stdin(text):
        buffer = io.BytesIO(text.encode())
        fobj = io.TextIOWrapper(buffer)
        monkeypatch.setattr(sys, "stdin", fobj)

    return set_stdin
