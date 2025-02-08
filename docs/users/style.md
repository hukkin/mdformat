# Formatting style

This document describes, demonstrates, and rationalizes the formatting style that mdformat follows.

Mdformat's formatting style is crafted so that writing, editing and collaborating on Markdown documents is as smooth as possible.
The style is consistent, and minimizes diffs (for ease of reviewing changes),
sometimes at the cost of some readability.

Mdformat makes sure to only change style, not content.
Once converted to HTML and rendered on screen,
formatted Markdown should yield a result that is visually identical to the unformatted document.
Mdformat CLI includes a safety check that will error and refuse to apply changes to a file
if Markdown AST is not equal before and after formatting.

Mdformat reads and writes all files with Utf-8 encoding.

## Headings

For consistency, only ATX headings are used.
Setext headings are reformatted using the ATX style.
ATX headings are used because they can be consistently used for any heading level,
whereas setext headings only allow level 1 and 2 headings.

Input:

```markdown
First level heading
===

Second level heading
---
```

Output:

```markdown
# First level heading

## Second level heading
```

## Bullet lists

Mdformat uses `-` as the bullet list marker.
In the case of consecutive bullet lists,
mdformat alternates between `-` and `*` markers.

## Ordered lists

Mdformat uses `.` as ordered list marker type.
In the case of consecutive ordered lists,
mdformat alternates between `.` and `)` types.

Mdformat uses `1.` or `1)` as the ordered list marker, also for noninital list items.

Input:

```markdown
1. Item A
2. Item B
3. Item C
```

Output:

```markdown
1. Item A
1. Item B
1. Item C
```

This "non-numbering" style was chosen to minimize diffs. But how exactly? Lets imagine we are listing the alphabets, using a proper consecutive numbering style:

```markdown
1. b
2. c
3. d
```

Now we notice an error was made, and that the first character "a" is missing.
We add it as the first item in the list.
As a result, the numbering of every subsequent item in the list will increase by one,
meaning that the diff will touch every line in the list.
The non-numbering style solves this issue: only the added line will show up in the diff.

Mdformat allows consecutive numbering via configuration.

## Code blocks

Only fenced code blocks are allowed.
Indented code blocks are reformatted as fenced code blocks.

Fenced code blocks are preferred because they allow setting an info string,
which indented code blocks do not support.

## Code spans

Length of a code span starting/ending backtick string is reduced to minimum.
Needless space characters are stripped from the front and back,
unless the content contains backticks.

Input:

`````markdown
````Backtick string is reduced.````

` Space is stripped from the front and back... `

```` ...unless a "`" character is present. ````
`````

Output:

```markdown
`Backtick string is reduced.`

`Space is stripped from the front and back...`

`` ...unless a "`" character is present. ``
```

## Inline links

Redundant angle brackets surrounding a link destination will be removed.

Input:

```markdown
[Python](<https://python.org>)
```

Output:

```markdown
[Python](https://python.org)
```

## Reference links

All link reference definitions are moved to the bottom of the document,
sorted by label. Unused and duplicate references are removed.

Input:

```markdown
[dupe ref]: https://gitlab.com
[dupe ref]: link1
[unused ref]: link2

Here's a link to [GitLab][dupe ref]
```

Output:

```markdown
Here's a link to [GitLab][dupe ref]

[dupe ref]: https://gitlab.com
```

## Paragraph word wrapping

Mdformat by default will not change word wrapping.
The rationale for this is to encourage and support [Semantic Line Breaks](https://sembr.org/),
a technique described by Brian Kernighan in the early 1970s,
yet still as relevant as ever today:

> **Hints for Preparing Documents**
>
> Most documents go through several versions (always more than you
> expected) before they are finally finished. Accordingly, you should
> do whatever possible to make the job of changing them easy.
>
> First, when you do the purely mechanical operations of typing, type
> so subsequent editing will be easy. Start each sentence on a new line.
> Make lines short, and break lines at natural places, such as after
> commas and semicolons, rather than
> randomly. Since
> most people change documents by rewriting phrases and adding, deleting
> and rearranging sentences, these precautions simplify any editing you
> have to do later.
>
> _— Brian W. Kernighan. "UNIX for Beginners". 1974_

Mdformat allows removing word wrap or setting a target wrap width via configuration.

## Thematic breaks

Thematic breaks are formatted as a 70 character wide string of underscores.
A wide thematic break is distinguishable,
and visually resembles how a corresponding HTML `<hr>` tag is typically rendered.

## Whitespace

Mdformat applies consistent whitespace across the board:

- Convert line endings to a single newline character
- Strip paragraph trailing and leading whitespace
- Indent contents of block quotes and list items consistently
- Always separate blocks with a single empty line
  (an exception being tight lists where the separator is a single newline character)
- Always end the document in a single newline character
  (an exception being an empty document)

## Hard line breaks

Hard line breaks are always a backslash preceding a line ending.
The alternative syntax,
two or more spaces before a line ending,
is not used because it is not visible.

Input:

```markdown
Hard line break is here:   
Can you see it?
```

Output:

```markdown
Hard line break is here:\
Can you see it?
```
