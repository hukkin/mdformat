from mdformat._util import is_md_equal


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
