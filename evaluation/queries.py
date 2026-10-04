"""Retrieval test set: adjuster-style questions with the clause number that answers them.

Written by the author in plain language, deliberately avoiding the clause wording so lexical
overlap alone does not solve them. They have not been validated by claims handlers; treat the
retrieval numbers as a comparison between methods on one test set, not as field accuracy.
"""

QUERIES = [
    # 2.1 collision
    ("Is damage from hitting another car covered?", "2.1"),
    ("Car crashed into a wall while parking, do we pay the repair?", "2.1"),
    ("Hit a deer on the motorway, is that included?", "2.1"),
    ("How much is deducted from the payout before we settle?", "2.1"),
    ("Someone reversed into the customer at a junction", "2.1"),
    # 2.2 settlement limit
    ("The repair costs more than the car is worth, what is the maximum?", "2.2"),
    ("Is the settlement limited to what the vehicle is worth?", "2.2"),
    ("Total loss: what is the upper bound of the payment?", "2.2"),
    # 2.3 glass
    ("A stone cracked the windscreen on the autobahn", "2.3"),
    ("Does fixing a smashed side window hurt the bonus?", "2.3"),
    ("Panoramic roof shattered in a hailstorm", "2.3"),
    # 2.4 fire and theft
    ("The car was stolen from outside the house overnight", "2.4"),
    ("Engine bay caught fire on the drive", "2.4"),
    ("Someone tried to break in and damaged the ignition", "2.4"),
    # 2.5 recovery
    ("Who pays for the tow truck after the crash?", "2.5"),
    ("Vehicle not drivable, needs to be taken to a garage", "2.5"),
    # 2.6 malicious damage
    ("Paintwork was keyed in a car park", "2.6"),
    ("Vandals slashed the wing mirrors last night", "2.6"),
    # 2.7 keys
    ("Customer dropped the car key in a lake", "2.7"),
    ("Remote fob stolen, locks need changing", "2.7"),
    # 3.1 replacement vehicle (COMFORT and PREMIUM only)
    ("Can the customer get a hire car while theirs is in the garage?", "3.1"),
    ("How many days of courtesy car are included?", "3.1"),
    ("Does the policy give a loan vehicle during repairs?", "3.1"),
    # 3.2 new car replacement (PREMIUM only)
    ("Brand new car written off after three months, what do they get?", "3.2"),
    ("Is there new-for-old cover for a nearly new vehicle?", "3.2"),
    # 4.1 unlicensed
    ("Driver had no licence at the time of the accident", "4.1"),
    ("Person behind the wheel was not legally allowed to drive", "4.1"),
    ("The son was learning to drive and had no permit", "4.1"),
    # 4.2 impairment
    ("Breathalyser came back over the limit", "4.2"),
    ("Driver was drunk when the crash happened", "4.2"),
    ("The driver had taken narcotics before the collision", "4.2"),
    # 4.3 commercial use
    ("Car was being used for food delivery when it was hit", "4.3"),
    ("Vehicle was working as a taxi at the time", "4.3"),
    ("Driver was doing ride-share pickups", "4.3"),
    # 4.4 wear and tear
    ("Gearbox failed on its own, no accident", "4.4"),
    ("Tyre punctured by a nail", "4.4"),
    ("Clutch is worn out after 200,000 km", "4.4"),
    # 4.5 racing
    ("Damage happened during a track day at the Nürburgring", "4.5"),
    ("Accident while timing laps on a closed circuit", "4.5"),
    # 4.6 territorial
    ("Crash happened on holiday in Morocco", "4.6"),
    ("Are we liable for an accident in Turkey?", "4.6"),
    # 5.1 late notification
    ("Claimant reported the accident two months later", "5.1"),
    ("How long does the customer have to tell us about an incident?", "5.1"),
    # 5.2 police report
    ("Do we need the reference number from the officers who attended?", "5.2"),
    ("Police came to the scene, what must the claimant provide?", "5.2"),
    # 5.3 fraud / exaggeration
    ("Claimant inflated the repair bill, what happens to the claim?", "5.3"),
    ("Can we cancel the contract if the claim was made up?", "5.3"),
    # 5.4 evidence
    ("Can we insist on photos of the dent?", "5.4"),
    ("Customer refuses to send the garage invoice", "5.4"),
    # 6.1 injury
    ("Passenger hurt their neck, are hospital bills paid?", "6.1"),
    ("What is the limit for treatment costs of injured occupants?", "6.1"),
    ("Physiotherapy after whiplash, is it reimbursed?", "6.1"),
    # 7.1 no claims discount
    ("Will this at-fault claim make next year's premium go up?", "7.1"),
    ("Does paying this claim affect the bonus at renewal?", "7.1"),
    # guidelines
    ("Estimate is 14,000 euros, who needs to look at it?", "GL-1"),
    ("Expensive repair above ten thousand, does a senior handler check it?", "GL-1"),
    ("The risk model marked this claim as suspicious, what now?", "GL-2"),
    ("When do we send a case to the investigations unit?", "GL-2"),
    ("The form and the garage quote disagree, what should the handler do?", "GL-3"),
    ("Dates in two documents don't match", "GL-3"),
]
