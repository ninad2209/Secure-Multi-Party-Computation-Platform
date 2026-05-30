"""
smc_party.py
------------
This file is the heart of the SMC protocol.
Each student/party runs this code on their own computer.

The main job of this file is to take an expression like:
    alice_secret + bob_secret

and compute it WITHOUT anyone revealing their actual number.

"""


import json
from typing import Dict

from communication import Communication, sanitize_url_param
from expression import (
    Expression,
    Secret,
    Scalar,
    Addition,
    Subtraction,
    Multiplication
)
from protocol import ProtocolSpec
from secret_sharing import reconstruct_secret, share_secret, Share


PRIME = 1000000000039   


def is_pure_scalar(expr: Expression) -> bool:       #Checks if an expression has ONLY public constants and no secrets.
    
    if isinstance(expr, Scalar):           # a single Scalar is always pure
        return True

    if isinstance(expr, Secret):          # a Secret is never pure - it contains a hidden value
        return False

    
    if isinstance(expr, (Addition, Subtraction, Multiplication)):  # for +, -, * check if BOTH sides are pure if both sides have no secrets then the whole thing has no secrets
        return is_pure_scalar(expr.left) and is_pure_scalar(expr.right)

    return False

#Computes the actual value of a pure scalar expression. and only call this after checking is_pure_scalar() is True!
def evaluate_pure_scalar(expr: Expression) -> int:
    
    if isinstance(expr, Scalar):       # base case - just return the number
        return expr.value

    
    if isinstance(expr, Addition):     # recursive cases - compute left and right then combine
        left  = evaluate_pure_scalar(expr.left)
        right = evaluate_pure_scalar(expr.right)
        return (left + right) % PRIME

    if isinstance(expr, Subtraction):
        left  = evaluate_pure_scalar(expr.left)
        right = evaluate_pure_scalar(expr.right)
        return (left - right) % PRIME

    if isinstance(expr, Multiplication):
        left  = evaluate_pure_scalar(expr.left)
        right = evaluate_pure_scalar(expr.right)
        return (left * right) % PRIME

    return 0


class SMCParty:
    """
    One party (person) in the SMC protocol.

    Each person creates one of these and calls run() to
    participate in the secure computation.
    """

    def __init__(
            self,
            client_id: str,
            server_host: str,
            server_port: int,
            protocol_spec: ProtocolSpec,
            value_dict: Dict[Secret, int]
        ):
        
        self.client_id = client_id                                      # give the name e.g. "Alice"

        
        self.comm = Communication(server_host, server_port, client_id)  # this handles all network communication with the server

        self.protocol_spec = protocol_spec   # the protocol spec tells us what expression to compute and who the other parties are
        self.value_dict = value_dict         #  secret value that only a particular parties knows

       
        self.all_parties = protocol_spec.participant_ids   # list of all party names e.g. ["Alice", "Bob", "Charlie"]
        self.num_parties = len(self.all_parties)           # gives no of parties in this computation

        
        self.secret_share_cache: Dict[str, Share] = {}    #"This cache stops the program from freezing when a secret is used more than once,because the network only sends each secret's data one time."

    def run(self) -> int:
       
        # This is the main function - call this to start the computation.
       
        my_final_share = self.process_expression(self.protocol_spec.expr)       # step 1: process the expression tree, get my piece of the answer
        result = self.publish_and_reconstruct("final", my_final_share)          # steps 2 and 3: publish my piece and reconstruct the real answer
        return result

    def get_op_label(self, expr_id) -> str:
        """
        Turns an expression id into a safe string for use in URLs.

        The expression ids are base64 encoded which can contain characters like +, /, = that break URLs.
        We replace them with safe characters.Eg-  "aB+c/D==" becomes "aB-c_D00"   """
        
        label = sanitize_url_param(expr_id)          # sanitize_url_param replaces + with - and / with _
        
        label = label.replace("=", "0")               # replace = with 0 because = breaks Flask URL routing
        return label

    def i_am_first_party(self) -> bool:
        
        #Returns True if I am the first party alphabetically.

        #We use this to decide who adds public constants to the result because  only 1 party should add them, otherwise they get counted multiple times and the answer is wrong.

        return self.client_id == sorted(self.all_parties)[0]

    def publish_and_reconstruct(self, label: str, my_share: Share) -> int:
        """
        This function does three things:
            1. I publish MY share on the server so everyone can see it
            2. I collect everyone else's shares from the server
            3. I add all shares together to get the real number

        This is how we get the final answer without revealing any parties i/p secret
        """
        
        self.comm.publish_message(label, json.dumps(my_share.serialize()))       # step 1: publish my share with a label so others can find it

        
        all_shares = []                                      
        for party_name in self.all_parties:                 # step 2: collect one share from every party (including self)
            raw_data = self.comm.retrieve_public_message(party_name, label)
            value    = json.loads(raw_data.decode())
            all_shares.append(Share.deserialize(value))

        
        return reconstruct_secret(all_shares)             # step 3: add them all together to get the real answer

    def process_expression(self, expr: Expression) -> Share:
        
        # FAST PATH: if the whole subtree has no secrets at all, # we can just compute it locally without any network calls.
        # Example: Scalar(3) + Scalar(2) = 5, no network needed. The first party holds the full value, others hold zero.When everyone adds their shares: value + 0 + 0 = value.

        if is_pure_scalar(expr):
            scalar_value = evaluate_pure_scalar(expr)
            if self.i_am_first_party():
                return Share(scalar_value)  # I hold the real value
            else:
                return Share(0)             # others hold zero

       
        if isinstance(expr, Secret):                          # CASE 1: Secret -A private value owned by one party. The owner splits it into shares and sends one to each party.
            label = self.get_op_label(expr.id)

            # check if we already fetched this secret before this happens when the same secret appears twice in the tree e.g. alice * bob + alice * charlie  (alice appears twice)
            # then second time we just return the cached share
            if label in self.secret_share_cache:
                return self.secret_share_cache[label]

            if expr in self.value_dict:                                    # if I OWN this secret, I split it and send pieces to everyone
                secret_value = self.value_dict[expr]
                
                all_shares = share_secret(secret_value, self.num_parties)    # split my secret into one random-looking piece per party

                
                for index, party_name in enumerate(self.all_parties):    # send each party their piece privately
                    share_as_string = str(all_shares[index].serialize())
                    self.comm.send_private_message(party_name, label, share_as_string)

            raw_bytes   = self.comm.retrieve_private_message(label)      # everyone (including the owner) retrieves their private piece
            share_value = int(raw_bytes.decode("ASCII"))
            my_share    = Share(share_value)

            # save it so we don't fetch it again if this secret appears again later in the expression tree
            self.secret_share_cache[label] = my_share

            return my_share
    
        elif isinstance(expr, Addition):               # CASE 2: Addition  (left - right).Each party subtract the shares locally.
            left_share  = self.process_expression(expr.left)
            right_share = self.process_expression(expr.right)
            return left_share + right_share

        elif isinstance(expr, Subtraction):             # CASE 3: Subtraction  (left - right) .Each party subtract the shares locally.
            left_share  = self.process_expression(expr.left)
            right_share = self.process_expression(expr.right)
            return left_share - right_share

        # CASE 4 : MULTIPLICATION .Multiplication  has 2 cases 
        #1- locally each party multiplies if left/right side share is scalar .
        #2 - If both sides are secret then we need Beaver triplet which we get from ttp
        elif isinstance(expr, Multiplication):                     
            left_share  = self.process_expression(expr.left)
            right_share = self.process_expression(expr.right)

            # sub-case a: LEFT side is a pure scalar (public number) then its safe to just multiply our share by the scalar directly
            if is_pure_scalar(expr.left):
                scalar_value = evaluate_pure_scalar(expr.left)
                return right_share * Share(scalar_value)

            # sub-case a: RIGHT side is a pure scalar (public number)
            # e.g. alice_secret * Scalar(3)
            if is_pure_scalar(expr.right):
                scalar_value = evaluate_pure_scalar(expr.right)
                return left_share * Share(scalar_value)
            
            #sub case b If both sides are secret then we need beaver triple protocol and our TTP gives us shares of (a, b, c) where c = a*b 

            # get a unique label for this multiplication node
            op_label = self.get_op_label(expr.id)

            # ask the trusted third party for our Beaver triple shares
            a_share, b_share, c_share = self.comm.retrieve_beaver_triplet_shares(op_label)

            # compute d = x - a  and  e = y - b
            d_share = left_share  - a_share
            e_share = right_share - b_share

            # reveal d and e to everyone (safe to reveal these)
            d = self.publish_and_reconstruct(op_label + "_d", d_share)
            e = self.publish_and_reconstruct(op_label + "_e", e_share)

            # each party computes their share of the result
            # formula: z_i = d*b_i + e*a_i + c_i
            term1    = b_share * Share(d)   # d * my b share
            term2    = a_share * Share(e)   # e * my a share
            term3    = c_share              # my c share
            my_z_share = term1 + term2 + term3

            # only the first party adds d*e because it is a public number
            if self.i_am_first_party():
                de= (d * e) % PRIME
                my_z_share = my_z_share + Share(de)

            return my_z_share

       
        
        else:               # we go back: something went wrong if we get here
            print("ERROR: do not know how to handle this expression type:", type(expr))
            return Share(0)