"""
expression.py
-------------
This file is about building math expressions for our SMC system.

Instead of computing things directly, we first BUILD a tree of
what we want to compute, then run it through the SMC protocol.

For example:
    alice_secret = Secret()
    bob_secret   = Secret()
    expr = alice_secret + bob_secret   <- this builds an Addition node

Think of it like a recipe. We write down WHAT to compute first,
then the SMC engine figures out HOW to compute it privately.
"""

import base64
import random
from typing import Optional


# each node in our expression tree gets a random 4 byte id so we can identify it on the network
ID_BYTES = 4


def gen_id() -> bytes:
    # make a random id using 4 random bytes then encode to text and base64 turns random bytes into readable characters like "aBcD=="
    id_bytes = bytearray(random.getrandbits(8) for _ in range(ID_BYTES))
    return base64.b64encode(id_bytes)


class Expression:
    """
    This is the parent class for everything in our expression tree.
    Secret, Scalar, Addition, Subtraction, Multiplication all inherit from it.

    The most important thing this class does is define +, -, *
    so we can write natural math like:
        alice_secret + bob_secret
        my_grade * Scalar(3)
    """

    def __init__(self, id: Optional[bytes] = None):
        # if no id is given, generate a fresh random one
        if id is None:
            id = gen_id()
        # save the id - every node needs one so the network can find it
        self.id = id

    def __add__(self, other):
        # this runs when we write:  a + b
        # it creates an Addition node with a on the left and b on the right
        return Addition(self, other)

    def __sub__(self, other):
        # this runs when we write:  a - b
        return Subtraction(self, other)

    def __mul__(self, other):
        # this runs when we write:  a * b
        return Multiplication(self, other)

    def __hash__(self):
        # python needs this so we can use Expression objects as dict keys
        # for example:  my_dict[alice_secret] = 80
        # without this python would not know how to look up alice_secret
        return hash(self.id)

    def __eq__(self, other):
        # two expressions are the same if they have the same id
        # this works together with __hash__ above
        if isinstance(other, Expression):
            return self.id == other.id
        return False


class Scalar(Expression):
    
    #A public constant number that EVERYONE knows.

    def __init__(self, value: int, id: Optional[bytes] = None):
        # save the actual number
        self.value = value
                                    
        super().__init__(id)         # call parent __init__ to get an id

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.value)})"   # this is just for printing nicely in the terminal


class Secret(Expression):
    """
    A private number that only ONE party knows.
    For example alice_secret = Secret() means Alice has a number that she keeps to herself.

    The Secret object does not store the actual value here.
    The actual value goes into value_dict when we run the protocol.
    """

    def __init__(self, id: Optional[bytes] = None):     # just call parent __init__ to get a unique id
        
        super().__init__(id)

    def __repr__(self):
        return "Secret()"


class Addition(Expression):
    """
    Represents left + right in our expression tree.
    Created automatically when you write:  a + b
    """

    def __init__(self, left, right):
        self.left  = left   # left side of the Addition
        self.right = right  # right side of the Addition
        super().__init__()  # get a fresh id for this node

    def __repr__(self):
        return f"({self.left} + {self.right})"


class Subtraction(Expression):
    """
    Represents left - right in our expression tree.
    Created automatically when you write:  a - b
    """

    def __init__(self, left, right):
        self.left  = left   # left side of the Sub
        self.right = right  # right side of the Sub
        super().__init__()

    def __repr__(self):
        return f"({self.left} - {self.right})"


class Multiplication(Expression):
    """
    Represents left * right in our expression tree.
    Created automatically when you write:  a * b

    If both sides are Secrets this triggers the Beaver triple protocol.
    If one side is a Scalar it is just local multiplication.
    """

    def __init__(self, left, right):
        self.left  = left   # left side of the Mul
        self.right = right  # right side of the Mul
        super().__init__()

    def __repr__(self):
        return f"({self.left} * {self.right})"