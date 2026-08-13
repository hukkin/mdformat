import sys

from mdformat._util import DEFAULT_MAX_NESTING, is_md_equal, required_nesting_depth
from tests.utils import nested_list_markdown


def test_is_md_equal():
    md1 = """
paragraph

```js
console.log()
```

paragr
"""
    md2 = """
paragraph

```js
bonsole.l()g
```

paragr"""
    assert not is_md_equal(md1, md2)
    assert is_md_equal(md1, md2, codeformatters=("js", "go"))


def test_is_md_equal__not():
    md1 = """
```js
console.log()
```

paragr

```js
console.log()
```
"""
    md2 = """
```js
bonsole.l()g
```

A different paragraph

```js
console.log()
```
"""
    assert not is_md_equal(md1, md2)
    assert not is_md_equal(md1, md2, codeformatters=("js",))


def test_required_nesting_depth__scales_with_actual_nesting():
    shallow_depth = required_nesting_depth(nested_list_markdown(1))
    deep_depth = required_nesting_depth(nested_list_markdown(30))

    assert shallow_depth is not None
    assert deep_depth is not None
    assert shallow_depth < deep_depth


def test_required_nesting_depth__exceeds_default_max_nesting_for_deep_lists():
    text = nested_list_markdown(30)

    depth = required_nesting_depth(text)

    assert depth is not None
    assert depth > DEFAULT_MAX_NESTING


def test_required_nesting_depth__recursion_limit_exceeded():
    original_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(50)

    try:
        assert required_nesting_depth(nested_list_markdown(50)) is None
    finally:
        sys.setrecursionlimit(original_limit)
