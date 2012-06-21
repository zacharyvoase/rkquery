from nose.tools import assert_raises

import rkquery


class ExampleQueryNode(rkquery.QueryNode):
    __slots__ = ('a', 'b', 'c')


def test_QueryNode_init():
    # Too few arguments
    assert_raises(TypeError, ExampleQueryNode, 1)
    assert_raises(TypeError, ExampleQueryNode, 1, 2)

    # Too many positional arguments
    assert_raises(TypeError, ExampleQueryNode, 1, 2, 3, 4)

    # Too many keyword arguments
    assert_raises(TypeError, ExampleQueryNode, 1, 2, 3, key=4)
    assert_raises(TypeError, ExampleQueryNode, 1, 2, 3, key=4, key2=5)

    # Exactly the right number of arguments
    node = ExampleQueryNode(1, 2, 3)
    assert node.a == 1
    assert node.b == 2
    assert node.c == 3
    node = ExampleQueryNode(1, 3, b=2)
    assert node.a == 1
    assert node.b == 2
    assert node.c == 3
    node = ExampleQueryNode(a=1, b=2, c=3)
    assert node.a == 1
    assert node.b == 2
    assert node.c == 3


def test_cannot_nest_boosts():
    boost1 = rkquery.Q("a").boost(5)
    boost2 = boost1.boost(10)
    assert boost2.root.node == boost1.root.node
    assert boost2.root.factor == 10


def test_cannot_nest_proximities():
    proxim1 = rkquery.Q("a").proximity(5)
    proxim2 = proxim1.proximity(10)
    assert proxim2.root.node == proxim1.root.node
    assert proxim2.root.proximity == 10


def test_and_is_commutative():
    first = rkquery.Q.all("A", "B") & rkquery.Q.all("C", "D")
    second = rkquery.Q.all("A", "B", "C", "D")
    assert unicode(first) == unicode(second)


def test_or_is_commutative():
    first = rkquery.Q.any("A", "B") | rkquery.Q.any("C", "D")
    second = rkquery.Q.any("A", "B", "C", "D")
    assert unicode(first) == unicode(second)


def test_not_not_x_is_x():
    # NOT (NOT x) => x
    x = rkquery.Q("Foo")
    not_x = ~x
    assert not_x.root.child is x.root
    not_not_x = ~not_x
    assert not_not_x.root is x.root


def test_field_not_becomes_not_field():
    # field:(NOT x) => NOT (field:x)
    field_not_x = rkquery.Q(username=~rkquery.Q("a"))
    assert isinstance(field_not_x.root, rkquery.Not)
    assert isinstance(field_not_x.root.child, rkquery.Field)
    assert field_not_x.root.child.field_name == "username"
    assert field_not_x.root.child.pattern == rkquery.Literal("a")
