"""
Custom SMC Application: Private Exam Grade Checker


Three students want to know class statistics about their exam
without telling each other their actual grades.
"""

import time
from multiprocessing import Process, Queue

from expression import Secret, Scalar
from protocol import ProtocolSpec
from server import run
from smc_party import SMCParty

PORT = 62222
PRIME = 1000000000039



def smc_client(client_id, prot, value_dict, queue):
    # each student runs this to do their part
    cli = SMCParty(client_id, "localhost", PORT,
                   protocol_spec=prot, value_dict=value_dict)
    result = cli.run()
    queue.put(result)
    print(f"    {client_id} finished!")


def smc_server(participant_list):
    # the trusted server - passes messages, never sees grades
    run("localhost", PORT, participant_list)


def run_smc(student_names, expression, value_dicts):
    """
    Runs ONE SMC computation using the already-running server.
    We do NOT start or stop the server here anymore.
    The server is started once in main() and stays running.
    """
    queue = Queue()
    protocol = ProtocolSpec(expr=expression, participant_ids=student_names)

    # create one process per student
    clients = [
        Process(target=smc_client,args=(student_names[i],protocol,value_dicts[i],queue))
        for i in range(len(student_names))
    ]

    # start all students
    for client in clients:
        client.start()

    # wait for all students to finish
    for client in clients:
        client.join()

    # collect results
    results = [queue.get() for _ in clients]

    return results



# CIRCUIT 1 - Addition of secrets eg- Alice+Bob+Charlie

def circuit1_total_sum(student_names, grades):
    print("\n--- Circuit 1: Total Sum of All Grades ---")

    # create a secret for each student's grade
    alice_secret   = Secret()
    bob_secret     = Secret()
    charlie_secret = Secret()

    # add all three grades together
    expression = alice_secret + bob_secret + charlie_secret

    # each student only gives their OWN grade
    value_dicts = [
        {alice_secret:   grades["Alice"]},
        {bob_secret:     grades["Bob"]},
        {charlie_secret: grades["Charlie"]},
    ]

    results = run_smc(student_names, expression, value_dicts)
    total = results[0]

    expected = grades["Alice"] + grades["Bob"] + grades["Charlie"]
    print(f"  Total   : {total}")
    print(f"  Expected: {expected}")
    assert total == expected
    print("Test Case 1 - PASSED")
    return total



# CIRCUIT 2 - Adding of secrets + scalar Constant
# The teacher gave everyone 5 bonus points .Eg: 240 + (5 x 3) = 255



def circuit2_total_with_bonus(student_names, grades, bonus_per_student):
    print("\n--- Circuit 2: Total Grades With Public Bonus ---")

    n = len(student_names)
    total_bonus = bonus_per_student * n

    print(f"  Bonus per student = {bonus_per_student}")
    print(f"  Total class bonus = {total_bonus}")

    alice_secret   = Secret()
    bob_secret     = Secret()
    charlie_secret = Secret()

    # sum of secret(i.e-grades) + Scalar(public bonus constant)
    expression = (
        alice_secret + bob_secret + charlie_secret
    ) + Scalar(total_bonus)

    value_dicts = [
        {alice_secret:   grades["Alice"]},
        {bob_secret:     grades["Bob"]},
        {charlie_secret: grades["Charlie"]},
    ]

    results = run_smc(student_names, expression, value_dicts)
    total = results[0]

    expected = sum(grades.values()) + total_bonus
    print(f"  Total with bonus : {total}")
    print(f"  Expected         : {expected}")
    assert total == expected
    print("  PASSED!")
    return total



# CIRCUIT 3 - Am I above or below the class average?
def circuit3_above_or_below_average(student_names, grades, my_name):
    print(f"\n--- Circuit 3: Is {my_name} Above or Below Average? ---")

    n = len(student_names)

    alice_secret   = Secret()
    bob_secret     = Secret()
    charlie_secret = Secret()

    secrets = {
        "Alice":   alice_secret,
        "Bob":     bob_secret,
        "Charlie": charlie_secret,
    }

    # total sum of all grades
    total_expression = alice_secret + bob_secret + charlie_secret

    # gap = my_grade * N - total
    gap_expression = (
        secrets[my_name] * Scalar(n)
    ) - total_expression

    value_dicts = [
        {alice_secret:   grades["Alice"]},
        {bob_secret:     grades["Bob"]},
        {charlie_secret: grades["Charlie"]},
    ]

    results = run_smc(student_names, gap_expression, value_dicts)
    gap = results[0]

    # convert large numbers back to negative
    if gap > PRIME // 2:
        gap = gap - PRIME

    expected = grades[my_name] * n - sum(grades.values())
    avg = sum(grades.values()) / n
    print(f"  Gap for {my_name}: {gap}")
    print(f"  Expected        : {expected}")

    if gap > 0:
        print(f"  Result: {my_name} is ABOVE average (average = {avg:.1f})")
    elif gap == 0:
        print(f"  Result: {my_name} is EXACTLY average (average = {avg:.1f})")
    else:
        print(f"  Result: {my_name} is BELOW average (average = {avg:.1f})")

    assert gap == expected
    print("  PASSED!")
    return gap

# CIRCUIT 4 - Best Study Group
def circuit4_best_study_group(student_names, grades, groups):

    print("\n--- Circuit 4: Best Study Group ---")
    print("Computing productivity scores privately...\n")

    # Create one secret for each student's grade
    grade_secrets = {name: Secret()for name in student_names}

    # Every participant provides only their own grade
    value_dicts = [{grade_secrets[name]: grades[name]} for name in student_names]

    group_scores = {}

    for group_name,members in groups.items():

        print(f"Evaluating {group_name}: {', '.join(members)}")

        # Build expression:
        # grade1 * grade2 * grade3 * ...
        expr = grade_secrets[members[0]]

        for member in members[1:]:
            expr = expr * grade_secrets[member]

        score = run_smc(student_names,expr,value_dicts)[0]

        group_scores[group_name] = score

        print(f"  Score = {score}")
        
        best_group = max(group_scores,key=group_scores.get)
        print("\nGroup Ranking:")
        
        ranking = sorted(group_scores.items(),key=lambda item: item[1],reverse=True)
        
        for pos,(group, score) in enumerate(ranking, start=1):
            print(f"  #{pos} {group:<15} score={score}")
            print(f"\nBest study group: {best_group}")
            
        return best_group,group_scores


# MAIN - starts the server ONCE then runs all circuits
if __name__ == "__main__":

   

    print("  Private Exam Grade Checker using SMC")
    print()
    print("Alice, Bob and Charlie got their exam results.")
    print("They want class stats but nobody shares their grade.")
    print()

    student_names = ["Alice", "Bob", "Charlie"]

    grades = {
        "Alice":   80,
        "Bob":     90,
        "Charlie": 70,
    }

    study_groups = {
    "Group A": ["Alice", "Charlie"],
    "Group B": ["Bob"]
    
    }
    bonus_per_student = 5
    
    
    print("Starting server...")      # Start the server 
    server = Process(target=smc_server, args=(student_names,))
    server.start()
    time.sleep(3)  # wait for server to be ready
    print("Server is running! Now running all circuits...\n")
    total          = circuit1_total_sum(student_names, grades)   # run all four circuits using the same server
    total_bonus    = circuit2_total_with_bonus(student_names, grades, bonus_per_student)

    gaps = {}
    for name in student_names:
        gaps[name] = circuit3_above_or_below_average(student_names, grades, name)

    best_group, group_scores = circuit4_best_study_group(student_names,grades,study_groups)
    
    print("\nAll circuits done. Shutting down server...")
    server.terminate()
    server.join()
    time.sleep(2)
    print("Server stopped.")

      
    avg = total / len(student_names)
 
    
    print("  FINAL RESULTS")
    print("=" * 60)
    print(f"  Students         : {', '.join(student_names)}")
    print(f"  Total grades     : {total}")
    print(f"  Class average    : {avg:.1f}")
    print(f"  Total + bonus    : {total_bonus}")
    print()
    for name in student_names:
        g = gaps[name]
        if g > 0:
            status = "above average"
        elif g == 0:
            status = "exactly average"
        else:
            status = "below average"
        print(f"  {name:<10} → {status}")
    print()
    
    print("\nStudy Group Scores")
    for group_name, score in group_scores.items():
        print(f"  {group_name:<15} : {score}")
        
    print(f"\nBest Study Group : {best_group}")
    

    print("  Nobody saw anyone else's grade. SMC worked!")
    print("  Ënd !!")