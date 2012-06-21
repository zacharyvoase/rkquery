rkQuery
=======

rkQuery is a library for programmatically building Riak search queries.
It aims to be easy to use, powerful, and protect from injection attacks
that would be possible with simple string interpolation.

Example
-------

Just start playing around with the ``q`` object. Literals (that is, raw
strings in queries) will be escaped if necessary:

::

    >>> from rkquery import q
    >>> q("some literal")
    <q: "some literal">
    >>> q(field="literal value")
    <q: field:"literal value">
    >>> q.not_(blocked="yes")
    <q: NOT blocked:yes>

You can provide multiple arguments, too. The default query combinator is
``AND``:

::

    >>> q("word1", "word2")
    <q: word1 AND word2>
    >>> q(username='foo', password='s3cr3t')
    <q: password:s3cr3t AND username:foo>

This is just a synonym for ``q.all()``:

::

    >>> q.all("word1", "word2")
    <q: word1 AND word2>
    >>> q.all(username='foo', password='s3cr3t')
    <q: password:s3cr3t AND username:foo>

You can construct ``OR`` queries using ``q.any()``:

::

    >>> q.any("word1", "word2")
    <q: word1 OR word2>
    >>> q.any(username='foo', email='foo@example.com')
    <q: email:"foo@example.com" OR username:foo>
    >>> q(field=q.any("string1", "string2"))
    <q: field:(string1 OR string2)>

Or by combining existing ``q`` objects with the bitwise logical
operators:

::

    >>> q.any("word1", "word2") & q("word3")
    <q: (word1 OR word2) AND word3>
    >>> q("word3") | q.all("word1", "word2")
    <q: (word1 AND word2) OR word3>
    >>> q.any(email="foo@example.com", username="foo") & q(password="s3cr3t")
    <q: (email:"foo@example.com" OR username:foo) AND password:s3cr3t>

There are helpers for negation as well (note that 'none' means 'not
any'):

::

    >>> q.none(blocked="yes", cheque_bounced="yes")
    <q: NOT (blocked:yes OR cheque_bounced:yes)>
    >>> ~q.any(blocked="yes", cheque_bounced="yes")
    <q: NOT (blocked:yes OR cheque_bounced:yes)>

You can do range queries with ``q.range()``:

::

    >>> q.range("red", "rum")
    <q: [red TO rum]>
    >>> q(field=q.range("red", "rum"))
    <q: field:[red TO rum]>

Note that the default is an *inclusive* range (square brackets). The
full set of range queries:

::

    >>> q.range_inclusive("red", "rum")
    <q: [red TO rum]>
    >>> q.range_exclusive("red", "rum")
    <q: {red TO rum}>
    >>> q.between("red", "rum")
    <q: {red TO rum}>

Term boosting is a simple unary operation:

::

    >>> q("red").boost(5)
    <q: red^5>

As is proximity:

::

    >>> q("See spot run").proximity(20)
    <q: "See spot run"~20>

