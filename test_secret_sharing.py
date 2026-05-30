"""
Unit tests for the secret sharing scheme.
Testing secret sharing is not obligatory.

MODIFY THIS FILE.
"""
from secret_sharing import Share, share_secret , reconstruct_secret

def test():
    secret=20
    num_parties=3

    shares=share_secret(secret,num_parties)
    #Check that we got the right number of shares back
    assert len(shares) == num_parties
    # Check that they are actual Share objects
    assert isinstance(shares[0], Share)
    
    # 3. Put them back together using your reconstruction function
    reconstructed = reconstruct_secret(shares)
    
    print(f"Original: {secret}, Reconstructed: {reconstructed}")
    
    # 4. Assert that the math holds up!
    assert reconstructed == secret
