strip paragraph lines
.
trailing whitespace 
at the end of paragraph lines 
should be stripped                   
.
trailing whitespace
at the end of paragraph lines
should be stripped
.

strip quotes
.
> Paragraph 1
> 
> Paragraph 2
.
> Paragraph 1
>
> Paragraph 2
.

no escape ampersand
.
R&B, rock & roll
.
R&B, rock & roll
.

list whitespaces
.
- item one
  
- item two
  - sublist
  
  - sublist
.
- item one

- item two

  - sublist

  - sublist
.

convert setext to ATX heading
.
Top level heading
=========

2nd level heading
---------
.
# Top level heading

## 2nd level heading
.

Lists with different bullets
.
- a
- b
* c
.
- a
- b

* c
.

numbered lists
.
1. a
2. b
3. c
   d
.
1. a
1. b
1. c
   d
.

numbered lists starting number
.
099. a
100. b
101. c
     d
.
99. a
01. b
01. c
    d
.

numbered lists nested
.
1. a
2. b
   1. x
   2. y
      z
.
1. a
1. b
   1. x
   1. y
      z
.

references:
.
[ref2]: link3 "title"

[text](link1) [text](link2 "title") [ref1] [ref2] [text][ref1]

![text](link1) ![text](link2 "title") ![ref1] ![ref2] ![text][ref1]

[ref1]: link4
[unused]: link5
.
[text](link1) [text](link2 "title") [ref1] [ref2] [text][ref1]

![text](link1) ![text](link2 "title") ![ref1] ![ref2] ![text][ref1]

[ref1]: link4
[ref2]: link3 "title"
.

thematic breaks
.
something something

---

something something
.
something something

______________________________________________________________________

something something
.

Ordered list marker type
.
1) a
2) b
1. x
2. y
.
1. a
1. b

1) x
1) y
.

Bullet list marker type
.
* a
* b
+ x
+ y
- c
- d
+ e
+ f
.
- a
- b

* x
* y

- c
- d

* e
* f
.

Empty list item
.
- next item is empty
- 
- whitespace should be stripped

1. next item is empty
1. 
1. whitespace should be stripped
.
- next item is empty
-
- whitespace should be stripped

1. next item is empty
1.
1. whitespace should be stripped
.

Empty ref link destination
.
[foo]: <>

[foo]
.
[foo]

[foo]: <>
.

Don't escape hash
.
- Recalculate secondary dependencies between rounds (#378)
.
- Recalculate secondary dependencies between rounds (#378)
.

Only escape first ")" and "."
.
1\) Only the first "\)" of a line should be escaped in this paragraph.

1\. Only the first "\." of a line should be escaped in this paragraph.

First \. or \) char should not be escaped here because this line does not look like a list.
.
1\) Only the first ")" of a line should be escaped in this paragraph.

1\. Only the first "." of a line should be escaped in this paragraph.

First . or ) char should not be escaped here because this line does not look like a list.
.

Don't escape list item marker if not followed by whitespace or end of line
.
1.No need to escape the dot here
1)No need to escape the closing bracket here
1. No need to escape the dot here (there is a no-break-space, not space)

This needs escaping (end of line after the dot)
 1.

This needs escaping (space after the closing bracket)
 1) 

.
1.No need to escape the dot here
1)No need to escape the closing bracket here
1. No need to escape the dot here (there is a no-break-space, not space)

This needs escaping (end of line after the dot)
1\.

This needs escaping (space after the closing bracket)
1\)
.

Escape line starting "+" and "-"
.
\+

\+No need to escape plus
+No need to escape plus

\-

\-No need to escape dash
-No need to escape dash
.
\+

+No need to escape plus
+No need to escape plus

\-

-No need to escape dash
-No need to escape dash
.


Escape ! preceding a link
.
We must escape the exclamation here \![link](https://www.debian.org/)!!!
.
We must escape the exclamation here \![link](https://www.debian.org/)!!!
.


Asterisk escapes
.
Escape*asterisk\*

Don't * escape * asterisk
.
Escape\*asterisk\*

Don't * escape * asterisk
.


Underscore escapes
.
Do _escape

Don't esc_ape

Don't _ escape _ underscore
.
Do _escape

Don't esc_ape

Don't _ escape _ underscore
.


Don't escape underscores that can't close emphasis
.
When using *target=_blank* the underscore is literal.

As a ______, I want X.

Set target=_blank or read foo._bar here.

Keep _a \_b c_ escaped inside emphasis.
.
When using *target=_blank* the underscore is literal.

As a ______, I want X.

Set target=_blank or read foo._bar here.

Keep _a \_b c_ escaped inside emphasis.
.


Keep shortcut reference links (dont convert to full reference)
.
![Image]

[iMaGe]: train.jpg

[Foo]

[fOO]: /url "title"
.
![Image]

[Foo]

[foo]: /url "title"
[image]: train.jpg
.


Empty document has no newline
.

.
.


Don't escape hash not followed by space
.
#No space after hash -> no need to escape
.
#No space after hash -> no need to escape
.


Indented raw HTML contains Markdown
.
  <center>

 - list item

  </center>
.
<center>

- list item

</center>
.

Autolink with percentage encoded space
.
<https://mytest.com/files/word%20document.docx>
.
<https://mytest.com/files/word%20document.docx>
.

Keep mailto: prefix in autolink
.
<MAILTO:FOO@BAR.BAZ>>
.
<MAILTO:FOO@BAR.BAZ>>
.

Tilde in info string
.
```~/.gitconfig
[user]
```
.
```~/.gitconfig
[user]
```
.

Info string starts with tilde and contains backtick
.
~~~\~`
123
~~~
.
~~~\~`
123
~~~
.

Keep inline HTML as inline, and block HTML as block
.
A
    <div>

A
   <div>
.
A
    <div>

A

<div>
.

Keep HTML blocks of type 7 unindented (they do not interrupt a paragraph)
.
text
<br/>
text
.
text
<br/>
text
.

sort digit references numerically
.
(References)[1] (should)[2] (sort)[10] (numerically)[word], if[🤪] they[⅕] are[𐩂] digits[!].

[🤪]: .
[2]: .
[word]: .
[10]: .
[⅕]: .
[1]: .
[𐩂]: .
[!]: .
.
(References)[1] (should)[2] (sort)[10] (numerically)[word], if[🤪] they[⅕] are[𐩂] digits[!].

[!]: .
[1]: .
[2]: .
[10]: .
[word]: .
[⅕]: .
[𐩂]: .
[🤪]: .
.

Unicode space (U+3000) after heading
.
# hoge
　

.
# hoge
.

Square bracket escapes
.
[no-escape]no [no-escape] no [\[\]](/url)

[escape]

[inline\](/url)

[link-label]

[link-label\]

[link-label\]: /url

[link-label]: /url
.
[no-escape]no [no-escape] no [[]](/url)

[escape]

\[inline\](/url)

[link-label]

\[link-label\]

\[link-label\]: /url

[link-label]: /url
.

Less than sign escapes
.
< no escape < no escape, now escape <
<

<
.
< no escape < no escape, now escape \<
\<

\<
.

Tabs to spaces
.
# Convert	tab	to	space	in			headings

Make a space	here.
.
# Convert tab to space in headings

Make a space here.
.

Reduce tabs and spaces to one space
.
# Reduce  		in			  	headings

Reduce to a space	 	here.
.
# Reduce in headings

Reduce to a space here.
.
