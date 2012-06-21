# rkQuery

rkQuery is a library for programmatically building Riak search queries. It aims
to be easy to use, powerful, and protect from injection attacks that would be
possible with simple string interpolation.


## Installation

    pip install rkquery


## Building Queries

Just start playing around with the ``Q`` object. Literals (that is, raw strings
in queries) will be escaped if necessary:

```pycon
>>> from rkquery import Q
>>> Q("some literal")
<Q: "some literal">
>>> Q(field="literal value")
<Q: field:"literal value">
>>> Q.not_(blocked="yes")
<Q: NOT blocked:yes>
```

You can provide multiple arguments, too. The default query combinator is `AND`:

```pycon
>>> Q("word1", "word2")
<Q: word1 AND word2>
>>> Q(username='foo', password='s3cr3t')
<Q: password:s3cr3t AND username:foo>
```

This is just a synonym for `Q.all()`:

```pycon
>>> Q.all("word1", "word2")
<Q: word1 AND word2>
>>> Q.all(username='foo', password='s3cr3t')
<Q: password:s3cr3t AND username:foo>
```

You can construct `OR` queries using `Q.any()`:

```pycon
>>> Q.any("word1", "word2")
<Q: word1 OR word2>
>>> Q.any(username='foo', email='foo@example.com')
<Q: email:"foo@example.com" OR username:foo>
>>> Q(field=Q.any("string1", "string2"))
<Q: field:(string1 OR string2)>
```

Or by combining existing `Q` objects with the bitwise logical operators:

```pycon
>>> Q.any("word1", "word2") & Q("word3")
<Q: (word1 OR word2) AND word3>
>>> Q("word3") | Q.all("word1", "word2")
<Q: (word1 AND word2) OR word3>
>>> Q.any(email="foo@example.com", username="foo") & Q(password="s3cr3t")
<Q: (email:"foo@example.com" OR username:foo) AND password:s3cr3t>
```

There are helpers for negation as well (note that 'none' means 'not any'):

```pycon
>>> Q.none(blocked="yes", cheque_bounced="yes")
<Q: NOT (blocked:yes OR cheque_bounced:yes)>
>>> ~Q.any(blocked="yes", cheque_bounced="yes")
<Q: NOT (blocked:yes OR cheque_bounced:yes)>
```

You can do range queries with `Q.range()`:

```pycon
>>> Q.range("red", "rum")
<Q: [red TO rum]>
>>> Q(field=Q.range("red", "rum"))
<Q: field:[red TO rum]>
```

Note that the default is an *inclusive* range (square brackets). The full set
of range queries:

```pycon
>>> Q.range_inclusive("red", "rum")
<Q: [red TO rum]>
>>> Q.range_exclusive("red", "rum")
<Q: {red TO rum}>
>>> Q.between("red", "rum")
<Q: {red TO rum}>
```

Term boosting is a simple unary operation:

```pycon
>>> Q("red").boost(5)
<Q: red^5>
```

As is proximity:

```pycon
>>> Q("See spot run").proximity(20)
<Q: "See spot run"~20>
```


## Running Queries

When you’ve built a query and you want to execute it, just call ``unicode()``
on it to get the full query string:

```pycon
>>> query = Q(field1="foo", field2="bar")
>>> unicode(query)
u'field1:foo AND field2:bar'
```

You can then use the standard Riak client search methods with this string.


## Unlicense

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
