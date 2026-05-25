"""
Secret sharing scheme.
MODIFY THIS FILE.
"""
from __future__ import annotations

from typing import List

import random 


PRIME=101    #ALL arithmetic happens modulo p .We choose a modulus prime p that is large.

class Share:
    """
    A secret share in a finite field.
    """

    def __init__(self, value):
        # Each party has one share of secret.
        self.value = value % PRIME                           

    def __repr__(self):
        # Helps with debugging. And its pretty printing for developers.
        return f"Share({self.value})"  

    def __add__(self, other):
        return Share((self.value + other.value) % PRIME)
        
    def __sub__(self, other):
        return Share((self.value - other.value) % PRIME)  

    def __mul__(self, other): 
        return Share((self.value * other.value) % PRIME)

    def serialize(self):
        """Generate a representation suitable for passing in a message."""
        raise NotImplementedError("You need to implement this method.")

    @staticmethod
    def deserialize(serialized) -> Share:
        """Restore object from its serialized representation."""
        


def share_secret(secret: int, num_shares: int) -> List[Share]:   #create random share and final share balances equation.
    """Generate secret shares."""
    shares = []
    for i in range(num_shares-1):
        random_value = random.randint(0, PRIME - 1)
        shares.append(Share(random_value))    
        print(random_value)                #create random share and append to list.

    total = sum(share.value for share in shares) 
    last_share = (secret - total) % PRIME    
    print(last_share)                                    # last_share=s-r1-r2 mod p 
    
    shares.append(Share(last_share))   #Append means adding the last share to the list of shares.
    return shares 


def reconstruct_secret(shares: List[Share]) -> int:
    """Reconstruct the secret from shares."""
    total = sum(share.value for share in shares)   # s=r1+r2+r3 mod p 
    return total % PRIME                            #return the secret.


if __name__ == "__main__":

    x_shares = share_secret(10, 3)

    print("Original shares:", x_shares)

    k = 5

    z_shares = x_shares.copy()

    z_shares[0] = z_shares[0] + Share(k)

    print("After adding constant:", z_shares)

    result = reconstruct_secret(z_shares)

    print("Final result:", result)

# Feel free to add as many methods as you want.
