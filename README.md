# Secure Multi-Party Computation Platform

A Python implementation of a Secure Multi-Party Computation (SMC) system
where multiple parties can jointly compute a function over their private
inputs without revealing those inputs to each other.

---

## What is SMC?

Imagine Alice, Bob and Charlie each have a private number like their exam
grade and they want to know the class average but nobody wants to share
their actual number.

SMC solves this. Each person splits their number into random looking pieces
called shares, sends the pieces to others, and everyone does math on their
piece locally. At the end the pieces are combined to get the final answer.
Nobody ever sees anyone elses actual number.

---

## Project Structure

```
├── expression.py               # Expression tree (Secret, Scalar, +, -, *)
├── secret_sharing.py           # Additive secret sharing scheme
├── smc_party.py                # Main SMC client for each party
├── ttp.py                      # Trusted parameter generator (Beaver triples)
├── server.py                   # Trusted server (not modified)
├── communication.py            # Network communication (not modified)
├── protocol.py                 # Protocol spec definition (not modified)
├── custom_app.py               # Custom application - grade checker
├── Custom_ApplicationReadme.md # Detailed custom app documentation
├── test_integration.py         # 10 integration tests
├── test_expression.py          # Expression tests
├── test_secret_sharing.py      # Secret sharing tests
├── test_ttp.py                 # TTP tests
└── requirements.txt            # Python dependencies
```

---

## What Was Implemented

### expression.py
Defines the arithmetic expression tree used to describe what to compute.
Supports Secret which is a private input owned by one party, Scalar which
is a public constant known to everyone, and Addition, Subtraction,
Multiplication for math operations.

Expressions are written naturally in Python:

```python
alice_secret = Secret()
bob_secret   = Secret()
expr = alice_secret + bob_secret * Scalar(3)
```

### secret_sharing.py
Implements additive secret sharing over a finite field modulo a large prime.

- `share_secret(secret, n)` splits a secret into n random looking shares
- `reconstruct_secret(shares)` adds all shares to recover the secret
- `Share` class represents one piece of a split secret

### ttp.py
Implements the Trusted Parameter Generator for Beaver triple multiplication.
When two secrets need to be multiplied, the TTP generates three random
numbers a, b, c where c = a times b and gives each party one share of each.
This allows Secret times Secret multiplication without revealing either secret.

### smc_party.py
The main SMC client that each party runs. It walks the expression tree
recursively, distributes secret shares to other parties, handles addition
and subtraction locally, uses Beaver triples for Secret times Secret
multiplication, and reconstructs the final result by combining all shares.

---

## How to Run

Install the required packages:

```
pip install -r requirements.txt
```

Run the integration tests:

```
pytest test_integration.py -v
```

All 10 tests should pass:

```
test_integration.py::test_suite1  PASSED   a + b + c
test_integration.py::test_suite2  PASSED   a - b
test_integration.py::test_suite3  PASSED   (a+b+c) * K
test_integration.py::test_suite4  PASSED   (a+b+c) + K
test_integration.py::test_suite5  PASSED   (a*K0 + b - c) + K1
test_integration.py::test_suite6  PASSED   a + b + c + d
test_integration.py::test_suite7  PASSED   (a*b) + (b*c) + (c*a)
test_integration.py::test_suite8  PASSED   ((a+K0) + b*K1 - c) * (d+e)
test_integration.py::test_suite9  PASSED   a1 + a2 + a3 + b
test_integration.py::test_suite10 PASSED   a*b*(15+15*3)
```

Run the custom application:

```
python custom_app.py
```

---

## Custom Application — Private Exam Grade Checker

### The Idea
Three students Alice, Bob and Charlie want to know class statistics about
their exam without telling each other their actual grades.

### What It Computes

| Circuit | What it does | SMC operations used |
|---------|-------------|-------------------|
| Circuit 1 | Total sum of all grades | Addition of secrets |
| Circuit 2 | Total grades plus public bonus points | Addition of secrets and Scalar constant |
| Circuit 3 | Is each student above or below average | Multiply by Scalar and subtract secrets |
| Circuit 4 | Best study group using grade times grade | Secret times Secret using Beaver triples |

### Why Circuit 4 Needs Beaver Triples
Circuit 4 computes alice_grade times bob_grade to find the best study pair.
Alice holds one secret and Bob holds the other which means two different
people hold the two numbers. They cannot multiply locally because each only
knows their own number. The Beaver triple protocol allows this multiplication
without either person revealing their grade.

### Threat Model
- Parties are honest but curious which means they follow the protocol
  correctly but try to learn as much as possible from the messages they see
- The SMC protocol guarantees no party learns anyone elses grade
- Only the final aggregate results are revealed to everyone

### What This Application Cannot Do

| Feature | Why not supported |
|---------|-----------------|
| Find highest or lowest grade | Needs comparison operators |
| Rank students by grade | Also needs comparisons |
| Compute exact division for average | Not supported in finite field SMC |
| Catch a cheating party | Needs zero knowledge proofs |

The workaround for average is to multiply by N instead of dividing which
gives the same above or below information without needing division.

---

## How the Beaver Triple Protocol Works

Normal multiplication does not work on shares:

```
share_x times share_y  is not equal to  share of (x times y)
```

Beaver triples fix this:

1. TTP generates random a, b, c where c = a times b
2. Each party gets one share of a, one share of b, one share of c
3. Parties compute d = x minus a and e = y minus b and reveal them publicly
4. Each party computes d times b_i plus e times a_i plus c_i
5. Only the first party adds d times e because it is a public number
6. All parties results add up to x times y

The values d and e are safe to reveal because they are masked by the
random values a and b so nobody can figure out x or y from them.

---

## Key Design Decisions

**Finite field arithmetic** — all math happens modulo a large prime
1000000000039 so values always stay in a safe range and wrap around
correctly for negative numbers.

**Secret share cache** — if the same Secret appears multiple times in
the expression tree we cache the share to avoid a network deadlock.
Without this the second fetch would wait forever because nobody sends
the share a second time.

**URL safe labels** — base64 ids are sanitized before use in URLs
because characters like plus, slash and equals break Flask URL routing
on Windows. We replace them with safe characters.

**Pure scalar fast path** — expressions with only Scalars and no Secrets
are computed locally without any network communication at all. This handles
cases like Scalar(15) plus Scalar(15) times Scalar(3) efficiently.

**Single server for all circuits** — in the custom application the server
is started once and reused for all four circuits instead of restarting it
every time. This saves significant time since starting a server takes
several seconds.

---

## Technologies Used

- Python 3.11
- Flask for the trusted server
- pytest for testing
- Multiprocessing so each party runs as a separate process

---

## Example Output

```
==================================================
  Private Exam Grade Checker using SMC
==================================================

--- Circuit 1: Total Sum of All Grades ---
  Total   : 240
  Expected: 240
  PASSED!

--- Circuit 2: Total Grades With Public Bonus ---
  Total with bonus : 255
  Expected         : 255
  PASSED!

--- Circuit 3: Is Alice Above or Below Average? ---
  Result: Alice is EXACTLY average (average = 80.0)
  PASSED!

--- Circuit 3: Is Bob Above or Below Average? ---
  Result: Bob is ABOVE average (average = 80.0)
  PASSED!

--- Circuit 3: Is Charlie Above or Below Average? ---
  Result: Charlie is BELOW average (average = 80.0)
  PASSED!

--- Circuit 4: Best Study Group ---
  Best study group: Alice and Bob
  Group score     : 7200
  PASSED!

==================================================
  FINAL RESULTS
==================================================
  Students         : Alice, Bob, Charlie
  Total grades     : 240
  Class average    : 80.0
  Total + bonus    : 255

  Alice      → exactly average
  Bob        → above average
  Charlie    → below average

  Best Study Group : Alice and Bob
  Nobody saw anyone else's grade. SMC worked!
==================================================
```

---

## Notes

- Python 3.11 is required. Newer versions may cause issues.
- Each test starts its own server process so the full test suite takes
  around 7 to 8 minutes to complete.
- The custom application takes around 5 minutes to run all four circuits.