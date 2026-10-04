"""Retrieval test set: adjuster-style questions with the clause number that answers them.

Written in plain language and deliberately avoiding the clause wording, so lexical overlap alone
does not solve them.
"""

QUERIES = [
    ("Is damage from hitting another car covered?", "2.1"),
    ("Car crashed into a wall while parking, do we pay the repair?", "2.1"),
    ("Hit a deer on the motorway, is that included?", "2.1"),
    ("How much is deducted from the payout before we settle?", "2.1"),
    ("The repair costs more than the car is worth, what is the maximum?", "2.2"),
    ("Is the settlement limited to what the vehicle is worth?", "2.2"),
    ("Total loss: what is the upper bound of the payment?", "2.2"),
    ("Driver had no licence at the time of the accident", "4.1"),
    ("Person behind the wheel was not legally allowed to drive", "4.1"),
    ("Breathalyser came back over the limit", "4.2"),
    ("Driver was drunk when the crash happened", "4.2"),
    ("The driver had taken narcotics before the collision", "4.2"),
    ("Car was being used for food delivery when it was hit", "4.3"),
    ("Vehicle was working as a taxi at the time", "4.3"),
    ("Claimant reported the accident two months later", "5.1"),
    ("How long does the customer have to tell us about an incident?", "5.1"),
    ("Do we need the reference number from the officers who attended?", "5.2"),
    ("Police came to the scene, what must the claimant provide?", "5.2"),
    ("Passenger hurt their neck, are hospital bills paid?", "6.1"),
    ("What is the limit for treatment costs of injured occupants?", "6.1"),
    ("Can the customer get a hire car while theirs is in the garage?", "3.1"),
    ("How many days of courtesy car are included?", "3.1"),
    ("Estimate is 14,000 euros, who needs to look at it?", "GL-1"),
    ("Expensive repair above ten thousand, does a senior handler check it?", "GL-1"),
    ("The risk model marked this claim as suspicious, what now?", "GL-2"),
    ("When do we send a case to the investigations unit?", "GL-2"),
    ("The form and the garage quote disagree, what should the handler do?", "GL-3"),
    ("Dates in two documents don't match", "GL-3"),
]
