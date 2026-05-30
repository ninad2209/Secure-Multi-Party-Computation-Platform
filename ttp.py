"""
ttp.py
------
TTP stands for Trusted Parameter Generator (Trusted Third Party).

Needed for Secret x Secret multiplication (Beaver triples).
"""

import random
from typing import Dict, Set, Tuple

from secret_sharing import share_secret, Share


PRIME = 1000000000039


class TrustedParamGenerator:
    """
    Generates Beaver triples for secret x secret multiplication.

    A Beaver triple is three numbers (a, b, c) where c = a * b.
    Each party gets one share of each number.

    """

    def __init__(self):
        self.participant_ids: Set[str] = set()   # stores all registered party names e.g. {"Alice", "Bob", "Charlie"}

        # stores the generated triples so every party gets shares of the SAME triple for the same operation
        # key:   operation id (string) value: dict mapping party name -> (a_share, b_share, c_share)
        self.triplet_dict: Dict = {}

    def add_participant(self, participant_id: str) -> None:
        self.participant_ids.add(participant_id)    # register a new party so we know how many shares to generate

    def retrieve_share(self, client_id: str, op_id) -> Tuple[Share, Share, Share]:
        """
        Returns this party's shares of the Beaver triple.

        If the triple for this operation does not exist yet,
        we generate it now and store it for the other parties.

        All parties calling this with the same op_id get shares
        of the SAME triple - this is very important!
        """

        # we convert op_id to a plain string as it can arrive as bytes or string depending on where it comes from
        if isinstance(op_id, bytes):
            op_id = op_id.decode("ASCII")
        op_id = str(op_id)

        # we make sure there are actually participants registered this should never happen but good to check
        if len(self.participant_ids) == 0:
            raise ValueError(
                "No participants registered! "
                "Call add_participant() before retrieve_share()."
            )

        # make sure this party is actually registered
        if client_id not in self.participant_ids:
            raise ValueError(
                f"Party '{client_id}' is not registered! "
                f"Known parties: {sorted(self.participant_ids)}"
            )

        # if we have not generated a triple for this operation yet, do it now
        if op_id not in self.triplet_dict:

            num_parties  = len(self.participant_ids)
            participants = sorted(list(self.participant_ids))     # sort party names so the order is always the same this ensures Alice always gets share index 0, Bob gets 1, etc.

            
            a = random.randint(0, PRIME - 1)   # pick two random numbers a and b
            b = random.randint(0, PRIME - 1)

            # compute c = a * b (this is the Beaver triple relationship)
            c = (a * b) % PRIME

            # split each of a, b, c into one share per party
            a_shares = share_secret(a, num_parties)
            b_shares = share_secret(b, num_parties)
            c_shares = share_secret(c, num_parties)

            
            self.triplet_dict[op_id] = {}         # store each party's three shares together
            for i, party_name in enumerate(participants):
                self.triplet_dict[op_id][party_name] = (
                    a_shares[i],   # this party's share of a
                    b_shares[i],   # this party's share of b
                    c_shares[i]    # this party's share of c
                )

        
        return self.triplet_dict[op_id][client_id]   # return just this party's shares of (a, b, c)