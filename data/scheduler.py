from datetime import datetime, timedelta
from data.connection import SessionLocal
from data.models import V2Drug, NotToTakeWith


def intervals_overlap(start1, dur1_h, start2, dur2_h):
    end1 = start1 + timedelta(hours=dur1_h)
    end2 = start2 + timedelta(hours=dur2_h)
    return max(start1, start2) < min(end1, end2)


# checks if putting the drug at the candidate time is valid
def constraints_ok(candidate_time, drug_id, schedule, drug_map, forbidden_pairs):
    current_drug = drug_map[drug_id]
    restricted = current_drug.restricted_time
    active_duration = restricted

    # minimum hours between doses of the same drug
    for entry in schedule:
        if entry["drug_id"] == drug_id:
            diff_hours = abs((candidate_time - entry["time"]).total_seconds()) / 3600.0
            if diff_hours < restricted:
                return False

    # incompatible drugs cannot be active at overlapping times
    for entry in schedule:
        other_id = entry["drug_id"]

        if (drug_id, other_id) in forbidden_pairs:
            other = drug_map.get(other_id)
            if other is None:
                continue

            other_duration = other.restricted_time

            # checks for each entry if the drug activity overlaps
            if intervals_overlap(candidate_time, active_duration,
                                 entry["time"], other_duration):
                return False

    return True


def build_schedule_for_patient(patient_id, required_doses, start_dt, end_dt, slot_minutes=60):
    session = SessionLocal()
    try:
        #load drug and drug id map for required doses
        drug_ids = [d["drug_id"] for d in required_doses]
        v2drugs = session.query(V2Drug).filter(V2Drug.drug_id.in_(drug_ids)).all()
        drug_map = {d.drug_id: d for d in v2drugs}

        # load forbidden pairs 
        interactions = session.query(NotToTakeWith).all()
        forbidden_pairs = set()
        for row in interactions:
            forbidden_pairs.add((row.drug_id_taking, row.drug_id_not_to_take_with))
            forbidden_pairs.add((row.drug_id_not_to_take_with, row.drug_id_taking))

        # build hourly slots
        slots = []
        current = start_dt
        delta = timedelta(minutes=slot_minutes)
        while current <= end_dt:
            slots.append(current)
            current += delta

        schedule = []

        # maybe give priority to medications with longer restricted times
        required_sorted = sorted(
            required_doses,
            key=lambda d: (drug_map[d["drug_id"]].restricted_time),
            reverse=True,
        )

        #figure out how many days are in the window
        #like start = 2025-12-01 08:00, end = 2025-12-03 07:59 is 3 days
        days_span = (end_dt.date() - start_dt.date()).days + 1
        window_days = max(1, days_span)

        # greedy sched, used help from chat to schedule for multiple days
        for day_index in range(window_days):
            # Compute the start/end for this specific day
            day_date = start_dt.date() + timedelta(days=day_index)
            day_start = datetime.combine(day_date, start_dt.time())
            if day_start > end_dt:
                break  # safety guard

            # End of this day (but don't go past global end_dt)
            day_end = min(day_start + timedelta(days=1) - delta, end_dt)

            # All slots that fall on this day
            day_slots = [s for s in slots if day_start <= s <= day_end]

            # For this day, try to schedule times_per_day doses for each drug
            for rd in required_sorted:
                drug_id = rd["drug_id"]
                times_per_day = rd["times_per_day"]

                for _ in range(times_per_day):
                    placed = False

                    for candidate in day_slots:
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
                        print(f"Could not find a valid slot for drug {drug_id} on {day_date}")

        return schedule

    finally:
        session.close()
