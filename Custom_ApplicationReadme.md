# Custom SMC Application: Private Exam Grade Checker

## 1. Introduction

Custom Application to see how we can use Secure Multi-Party Computation in real world scenario.

The application is called  Exam Grade Checker.The goal of the application is to allow students to learn useful class statistics without revealing their actual grades to one another.

In this scenario there are 3 students (Alice, Bob and Charlie)  who have received their exam results.They want to learn information such as the total class score,class average and how their performance compares to the rest of the class.However,no one wants to reveal their grades to one another

Using Secure Multi-Party Computation,each student contributes their private input while only the final result of the computation becomes visible. Individual grades remain hidden throughout the entire protocol.

For demonstration purposes, the following grades are used:

| Student | Grade (Private) |
| ------- | --------------- |
| Alice   | 80              |
| Bob     | 90              |
| Charlie | 70              |

The teacher also awards a public bonus of 5 points to every student.

---

## 2. Motivation

Student grades are sensitive personal information.In many situations,students may wish to compare their performance against the class without revealing their grades.

In this scenario we have test cases like 

1 - Finding the class average.
2 Determining whether a student performed above or below average.
3 - Comparing the performance of study groups.
4- Producing anonymous class statistics.

Traditionally,a trusted third party would need access to all grades in order to perform these calculations.Secure Multi-Party Computation removes this requirement by allowing the computation to be performed directly on secret-shared values.

---

## 3. Threat Model 

We assume the parties to be honest but curious then ttp is responsible for creating the Beaver triplets and distributing the shares

### Security Goal

No student should learn:

* Another student's grade.
* Intermediate secret values.
* Shares owned by other student.

Only the final computation result is revealed.

---

## 4. Implemented Circuits

The application contains four different circuits which demonstrate the major operations supported by the SMC engine.

### Circuit 1 – Total Sum of Grades   Additions of the secret values

This circuit computes the total score of all students.

Expression:

Total = Alice + Bob + Charlie =80 + 90 + 70 = 240  (using the same numbers in our example)

### Circuit 2 – Total Grades with Public Bonus  Addition of secret + Scalar

The teacher awards a public bonus of five marks to every student.

Expression: Total + (Bonus × Number of Students)       240 + (5 × 3) = 255     Using the example values:

---

### Circuit 3 – Above or Below Average   (Local Multiplication & Subtraction)

This circuit determines whether a student's performance is above, equal to or below the class average.

Expression - (Student Grade × Number of Students) − Total Grade Sum

Interpretation:

* Result > 0 → Above average
* Result = 0 → Exactly average
* Result < 0 → Below average

Example for Alice:

(80 × 3) − 240 = 0

Therefore, Alice is exactly at the class average.


### Circuit 4 – Study Group Productivity Comparison  (Multiplication using Beaver triplets)

The final circuit evaluates the performance of study groups.

A study group receives a productivity score equal to the product of all grades within the group.

For eg: Group A = {Alice, Charlie} Score = 80 × 70 = 5600  Group B = {Bob} Score = 90 

The study group with the highest productivity score is considered the strongest-performing group.

Alice's grade is known only to Alice & Bob's grade is known only to Bob.

Computing: Alice Grade × Bob Grade requires multiplication between two secret values owned by different participants.This operation cannot be performed locally and therefore uses the Beaver Triple protocol implemented in the SMC engine.

## 5. Design Decisions

Several design decisions were made during implementation.

1-  No Division Operation- The implemented SMC engine does not support secure division between secret values because of this the Circuit 3 uses an equivalent comparison expression instead of directly computing the average.

2- Public Final Results - The application reveals only the final computation result.Intermediate values remain secret and are never reconstructed.

3- General Study Group Design -The study-group circuit was implemented in a generic way so that any number of groups and participants can be evaluated without modifying the core protocol logic.This makes the application reusable for future scenarios beyond the three-student example.

## 6. Testing

Each circuit contains validation checks comparing the SMC result against a locally computed expected result.

Assertions are used to verify correctness.

Example:

SMC Result = 240 ,Expected Result = 240 If both values match,the circuit passes successfully.

This helps to ensure that the secure computation produces the same output as normal arithmetic while maintaining privacy.

## 7. Conclusion

The Private Exam Grade Checker demonstrates how Secure Multi-Party Computation can be applied to a realistic privacy-sensitive problem.

The application successfully uses the implemented SMC engine to compute:

1- Total class grades
2- Grades including public bonuses
3- Above/below-average performance
4- Study-group productivity scores

while ensuring that no participant learns another participant's private grade.

The application demonstrates the use of addition, subtraction, scalar operations, and Beaver-triple-based secret multiplication which cover all major operation of SMC
