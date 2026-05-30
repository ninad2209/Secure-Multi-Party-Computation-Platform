"""
Unit tests for expressions.
Testing expressions is not obligatory.

MODIFY THIS FILE.
"""

from expression import Secret, Scalar


# Example test, you can adapt it to your needs.
def test_expr_construction():
    a = Secret(b"1")
    b = Secret(b"2")
    c = Secret(b"3")
    expr = (a + b) * c * Scalar(4) + Scalar(3)
    print("Generated expression look like :",repr(expr))


    assert repr(expr) == "((((Secret()+Secret())*Secret())*Scalar(4))+Scalar(3))"


def test_multiplication():
    a=Secret(b"1")
    b=Secret(b"2")
    expr=a * b

    assert repr(expr) == "(Secret()*Secret())"
