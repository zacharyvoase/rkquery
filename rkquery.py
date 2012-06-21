"""
rkQuery is a library for programmatically building Riak search queries. It aims
to be easy to use, powerful, and protect from injection attacks that would be
possible with simple string interpolation.

Just start playing around with the ``Q`` object:

    >>> from rkquery import Q
    >>> Q("some literal")
    <Q: "some literal">
    >>> Q(field="literal value")
    <Q: field:"literal value">
    >>> Q.not_(blocked="yes")
    <Q: NOT blocked:yes>

You can provide multiple arguments, too. The default query combinator is `AND`:

    >>> Q("word1", "word2")
    <Q: word1 AND word2>
    >>> Q(username='foo', password='s3cr3t')
    <Q: password:s3cr3t AND username:foo>

This is just a synonym for `Q.all()`:

    >>> Q.all("word1", "word2")
    <Q: word1 AND word2>
    >>> Q.all(username='foo', password='s3cr3t')
    <Q: password:s3cr3t AND username:foo>

Of course you can construct `OR` queries, using `Q.any()`:

    >>> Q.any("word1", "word2")
    <Q: word1 OR word2>
    >>> Q.any(username='foo', email='foo@example.com')
    <Q: email:"foo@example.com" OR username:foo>
    >>> Q(field=Q.any("string1", "string2"))
    <Q: field:(string1 OR string2)>

Or by combining existing `Q` objects:

    >>> Q.any("word1", "word2") & Q("word3")
    <Q: (word1 OR word2) AND word3>
    >>> Q("word3") | Q.all("word1", "word2")
    <Q: (word1 AND word2) OR word3>
    >>> Q.any(email="foo@example.com", username="foo") & Q(password="s3cr3t")
    <Q: (email:"foo@example.com" OR username:foo) AND password:s3cr3t>

There are helpers for negation as well (note that 'none' means 'not any'):

    >>> Q.none(blocked="yes", cheque_bounced="yes")
    <Q: NOT (blocked:yes OR cheque_bounced:yes)>
    >>> ~Q.any(blocked="yes", cheque_bounced="yes")
    <Q: NOT (blocked:yes OR cheque_bounced:yes)>

You can do range queries with `Q.range()`:

    >>> Q.range("red", "rum")
    <Q: [red TO rum]>
    >>> Q(field=Q.range("red", "rum"))
    <Q: field:[red TO rum]>

Note that the default is an *inclusive* range (square brackets). The full set
of range queries:

    >>> Q.range_inclusive("red", "rum")
    <Q: [red TO rum]>
    >>> Q.range_exclusive("red", "rum")
    <Q: {red TO rum}>
    >>> Q.between("red", "rum")
    <Q: {red TO rum}>

Term boosting is a simple unary operation:

    >>> Q("red").boost(5)
    <Q: red^5>

As is proximity:

    >>> Q("See spot run").proximity(20)
    <Q: "See spot run"~20>
"""

import itertools as it
import re


class Query(object):
    """
    A Riak query.

    This object represents a Riak query. You can add more constraints using the
    various methods and operators defined on this class.

    To get your generated query, just use ``unicode()``:

        >>> unicode(Q(field1="foo", field2="bar"))
        u'field1:foo AND field2:bar'
    """

    __slots__ = ('root', '__weakref__')

    def __init__(self, root):
        self.root = root

    def __repr__(self):
        return "<Q: %s>" % unicode(self.root)

    def __unicode__(self):
        return unicode(self.root)

    def __str__(self):
        return str(self.root)

    def __or__(self, other):
        if hasattr(self.root, '__or__'):
            return Query(self.root | make_node(other))
        return Query(Any((self.root, make_node(other))))

    def __and__(self, other):
        if hasattr(self.root, '__and__'):
            return Query(self.root & make_node(other))
        return Query(All((self.root, make_node(other))))

    def __invert__(self):
        if not hasattr(self.root, '__invert__'):
            return Query(Not(self.root))
        return Query(~self.root)

    def boost(self, factor):
        """Set the result importance factor of this term."""
        return Query(Boost(self.root, factor))

    def proximity(self, proximity):
        """Set a proximity for this term."""
        return Query(Proximity(self.root, proximity))


class QueryNode(object):
    """Query node base class."""

    __slots__ = ()
    # Is it safe to display this node without parentheses as part of a complex
    # query?
    no_parens = False

    def __init__(self, *args, **kwargs):
        argc = len(args) + len(kwargs)
        for slot in self.__slots__:
            if args and slot not in kwargs:
                setattr(self, slot, args[0])
                args = args[1:]
            elif slot in kwargs:
                setattr(self, slot, kwargs.pop(slot))
            else:
                raise TypeError("Expected argument for slot %r" % slot)
        if args:
            raise TypeError("Too many arguments (expected max %d, got %d)" % (
                len(self.__slots__), argc))
        elif kwargs:
            if len(kwargs) == 1:
                raise TypeError("Unexpected kwarg: %r" % kwargs.keys()[0])
            raise TypeError("Unexpected kwargs: %r" % kwargs.keys())

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        raise NotImplementedError

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return all(getattr(self, slot, None) == getattr(other, slot, None)
                   for slot in self.__slots__)

    def sort_key(self):
        """Return a tuple by which this node may be sorted."""
        return (unicode(self),)

    def parens(self):
        """Return a unicode representation, in parentheses."""
        if self.no_parens:
            return unicode(self)
        return u'(%s)' % unicode(self)


class Literal(QueryNode):
    __slots__ = ('string',)
    # string: the string itself
    no_parens = True

    def __unicode__(self):
        if self.needs_escaping(self.string):
            return self.escape(self.string)
        return self.string

    @staticmethod
    def escape(string):
        """Escape a literal string (without adding quotes)."""
        return u'"%s"' % (string
                          .replace(r'\\', r'\\\\')
                          .replace(r'"', r'\\"')
                          .replace(r'\'', r'\\\''))

    @staticmethod
    def needs_escaping(string):
        """Check if a string requires quoting or escaping."""
        return not re.match(r'^[A-Za-z0-9]+$', string)

    def sort_key(self):
        return (self.string,)


class Boost(QueryNode):
    __slots__ = ('node', 'factor')
    # node: the node to boost
    # factor: the factor by which to boost it

    def __init__(self, node, factor):
        self.factor = factor
        if isinstance(node, type(self)):
            self.node = node.node
        else:
            self.node = node

    def __unicode__(self):
        return u'%s^%d' % (self.node.parens(), self.factor)

    def sort_key(self):
        return self.node.sort_key()


class Proximity(QueryNode):
    __slots__ = ('node', 'proximity')
    # node: the term to apply a proximity search to
    # proximity: the size of the block in which to search

    def __init__(self, node, proximity):
        self.proximity = proximity
        if isinstance(node, type(self)):
            self.node = node.node
        else:
            self.node = node

    def __unicode__(self):
        return u'%s~%d' % (self.node.parens(), self.proximity)

    def sort_key(self):
        return self.node.sort_key()


class Field(QueryNode):
    __slots__ = ('field_name', 'pattern')
    # field_name: the name of the field to query against.
    # pattern: a QueryNode representing the pattern against the field.
    no_parens = True

    def __new__(cls, field_name, pattern):
        # field:(NOT x) => (NOT field:x)
        if isinstance(pattern, Not):
            return Not(cls(field_name, pattern.child))
        return QueryNode.__new__(cls, field_name, pattern)

    def __unicode__(self):
        return u'%s:%s' % (unicode(self.field_name), self.pattern.parens())

    def sort_key(self):
        return (self.field_name,) + self.pattern.sort_key()


class LogicalOperator(QueryNode):
    __slots__ = ('children',)
    operator = NotImplemented

    def __init__(self, children):
        self.children = tuple(sorted(children, key=lambda c: c.sort_key()))

    def __unicode__(self):
        return (u' %s ' % self.operator).join(
            child.parens() for child in self.children)

    def sort_key(self):
        return None


class Any(LogicalOperator):
    operator = 'OR'

    def __or__(self, other):
        if isinstance(other, type(self)):
            return type(self)(self.children + other.children)
        else:
            return type(self)(self.children + (other,))


class All(LogicalOperator):
    operator = 'AND'

    def __and__(self, other):
        if isinstance(other, type(self)):
            return type(self)(self.children + other.children)
        else:
            return type(self)(self.children + (other,))


class Not(QueryNode):
    __slots__ = ('child',)
    no_parens = True

    def __unicode__(self):
        return u'NOT %s' % self.child.parens()

    def __invert__(self):
        return self.child


class InclusiveRange(QueryNode):
    __slots__ = ('start', 'stop')
    no_parens = True

    def __unicode__(self):
        return u'[%s TO %s]' % (self.start.parens(), self.stop.parens())


class ExclusiveRange(QueryNode):
    __slots__ = ('start', 'stop')
    no_parens = True

    def __unicode__(self):
        return u'{%s TO %s}' % (self.start.parens(), self.stop.parens())


def make_node(obj):
    if isinstance(obj, Query):
        return obj.root
    elif isinstance(obj, QueryNode):
        return obj
    elif isinstance(obj, unicode):
        return Literal(obj)
    elif isinstance(obj, str):
        return Literal(obj.decode('utf-8'))
    elif isinstance(obj, tuple) and len(obj) == 2:
        return Field(obj[0], make_node(obj[1]))
    raise TypeError("Cannot make a query node from: %r" % (obj,))


def Q(*args, **kwargs):

    """
    Build Riak search queries safely and easily.

    This is the primary point of interaction with this library. For examples of
    how to use it, consult the docstring on the ``rkquery`` module.
    """

    return q_all(*args, **kwargs)


def combinator(name, c_type):
    def q_combinator(*args, **kwargs):
        argc = len(args) + len(kwargs)
        if argc == 1:
            if args:
                return Query(make_node(args[0]))
            else:
                return Query(make_node(kwargs.items()[0]))
        else:
            return Query(c_type(make_node(arg)
                            for arg in it.chain(args, kwargs.iteritems())))
    q_combinator.__name__ = name
    return q_combinator


q_any = combinator('q_any', Any)
q_all = combinator('q_all', All)


def q_none(*args, **kwargs):
    return ~q_any(*args, **kwargs)


def q_not(*args, **kwargs):
    return ~q_all(*args, **kwargs)


def q_inclusive_range(start, stop):
    return Query(InclusiveRange(make_node(start), make_node(stop)))


def q_exclusive_range(start, stop):
    return Query(ExclusiveRange(make_node(start), make_node(stop)))


Q.all = q_all
Q.any = q_any
Q.none = q_none
Q.not_ = q_not
Q.range = q_inclusive_range
Q.range_inclusive = q_inclusive_range
Q.range_exclusive = q_exclusive_range
Q.between = q_exclusive_range
