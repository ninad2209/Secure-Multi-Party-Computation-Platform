"""
secret_sharing.py
-----------------
This file handles the core math of secret sharing.

All math happens modulo a big prime number so everything stays inside a safe range.
"""

from __future__ import annotations
from typing import List
import random


# all our math happens inside this range (0 to PRIME-1)
PRIME = 1000000000039


class Share:
    """
    One piece of a split secret that belongs to one party.
    For example Share(31) means this party holds the value 31.
    """

    def __init__(self, value):                # keep the value inside valid range using mod after PRIME it wraps back to 0
        self.value = value % PRIME

    def __repr__(self):                # nice printing for debugging
        return f"Share({self.value})"

    def __add__(self, other):                              # adding two shares together (stays inside valid range)
        return Share((self.value + other.value) % PRIME)

    def __sub__(self, other):                              # subtracting two shares (stays inside valid range)
        return Share((self.value - other.value) % PRIME)

    def __mul__(self, other):            # multiplying two shares locally happens only when one of them is a constant for secret * secret we need beaver triplet
        return Share((self.value * other.value) % PRIME)

    def serialize(self):                # convert Share(80) to just the number 80 used when we send the share over the network
        return self.value

    @staticmethod
    def deserialize(value):                      # convert the number 80 back to Share(80),used when we receive a share from the network
        
        return Share(value)


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """
    Split one secret number into num_shares random looking pieces.

    How it works:
        - Generate (num_shares - 1) completely random numbers
        - Calculate the last number so everything adds up to secret
        - Return all the pieces

    Example: share_secret(80, 3)
        random share 1 = 31
        random share 2 = 55
        last share     = (80 - 31 - 55) mod PRIME = -6 mod PRIME
        result: [Share(31), Share(55), Share(big number)]
        they all add up to 80!
    """
    shares = []
    for i in range(num_shares - 1):                                # make (num_shares - 1) random shares
        random_value = random.randint(0, PRIME - 1)
        shares.append(Share(random_value))

    
    total_so_far = sum(share.value for share in shares)            # calculate the last share so everything adds up to secret
    last_share   = (secret - total_so_far) % PRIME
    shares.append(Share(last_share))

    return shares


def reconstruct_secret(shares: List[Share]) -> int:    
    total = sum(share.value for share in shares)               #Add all shares together to recover the original secret.
    return total % PRIME