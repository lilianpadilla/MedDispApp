from datetime import timedelta
from data.connection import SessionLocal
from data.models import V2Drug, NotToTakeWith


def intervals_overlap(start1, dur1_h, start2, dur2_h): #used ai for help here
    end1 = start1 + timedelta(hours=dur1_h)
    end2 = start2 + timedelta(hours=dur2_h)
    return max(start1, start2) < min(end1, end2)

#checks if putting the drug at the candidate time is valid
def constraints_ok(candidate_time, drug_id, schedule, drug_map, forbidden_pairs):
    current_drug = drug_map[drug_id]
    restricted = current_drug.restricted_time # hours
    active_duration = restricted # assume active for RestrictedTime hours

    # minimum hours between doses of the same drug
    for entry in schedule:
        if entry["drug_id"] == drug_id:
            diff_hours = abs((candidate_time - entry["time"]).total_seconds()) / 3600.0 #ai generated here
            if diff_hours < restricted:
                return False

    # incompatible drugs cannot be active at overlapping times
    for entry in schedule:
        other_id = entry["drug_id"]

        if (drug_id, other_id) in forbidden_pairs: # a bit complex 
            other = drug_map.get(other_id)
            if other is None:
                continue

            other_duration = other.restricted_time

            if intervals_overlap(candidate_time, active_duration, #checks  for each entry if the drug activity overlaps
                                 entry["time"], other_duration):
                return False

    return True


def build_schedule_for_patient(patient_id, required_doses, start_dt, end_dt, slot_minutes=60):
    session = SessionLocal()
    try: #required doses is a list of dictionaries
        drug_ids = [d["drug_id"] for d in required_doses] #get drug info for all user input
        v2drugs = session.query(V2Drug).filter(V2Drug.drug_id.in_(drug_ids)).all()
        drug_map = {d.drug_id: d for d in v2drugs}

        
        interactions = session.query(NotToTakeWith).all()
        forbidden_pairs = set() # set so we dont get pairs like (a,b) and (b,a) distinguished
        for row in interactions:
            forbidden_pairs.add((row.drug_id_taking, row.drug_id_not_to_take_with))
            forbidden_pairs.add((row.drug_id_not_to_take_with, row.drug_id_taking))

        
        slots = []
        #basically adding slots for every hour
        current = start_dt
        delta = timedelta(minutes=slot_minutes)
        while current <= end_dt:
            slots.append(current)
            current += delta

        schedule = []

        # maybe give priority to medications with longer restricted times??
        required_sorted = sorted(
            required_doses,
            key=lambda d: (drug_map[d["drug_id"]].restricted_time),
            reverse=True,
        )

        #greedy algo
        for rd in required_sorted:
            drug_id = rd["drug_id"]
            times_per_day = rd["times_per_day"]

            for _ in range(times_per_day):
                placed = False
                for candidate in slots:
                    if constraints_ok(candidate, drug_id, schedule, drug_map, forbidden_pairs):
                        schedule.append(
                            {
                                "drug_id": drug_id,
                                "time": candidate,
                                "quantity": 1,  # always 1
                            }
                        )
                        placed = True
                        break

                if not placed:
                    print(f"Could not find a valid slot for drug {drug_id}")

        return schedule

    finally:
        session.close()
