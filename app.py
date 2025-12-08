# app.py
from flask import Flask, jsonify, request, render_template
from datetime import datetime, date, time, timedelta

from data.connection import SessionLocal
from data.models import V2Drug
from data.scheduler import build_schedule_for_patient

app = Flask(__name__)


MAX_TIMES_PER_DAY = 24 # reasonable max
MAX_WINDOW_DAYS = 7 # 1–7 days


@app.route("/")
def home():
    return {"message": "hello from root /"}


@app.route("/drugs", methods=["GET"])
def get_drugs():
    """Debug/utility route: see all v2drug rows as JSON."""
    session = SessionLocal()
    drugs = session.query(V2Drug).all()
    session.close()
    
    return jsonify([
        {
            "drug_id": d.drug_id,
            "name": d.name,
            "restricted_time": d.restricted_time,
        }
        for d in drugs
    ])

#get reqs for form, post reqs for making sure inputs are valid and running + rendering sched
#used chatgpt for warning/error control
@app.route("/schedule", methods=["GET", "POST"])
def schedule_page():
    schedule = None
    error = None
    warnings = []

    if request.method == "POST":
        try:
            patient_id = request.form.get("patient_id")
            window_days_raw = request.form.get("window_days", "1")
            start_date_str = request.form.get("start_date")

            #valid inputs
            if not patient_id:
                error = "Patient ID is required."
                return render_template("schedule.html", schedule=None, error=error, warnings=warnings)
            
            try:
                window_days = int(window_days_raw)
            except ValueError:
                error = "Window (days) must be a number."
                return render_template("schedule.html", schedule=None, error=error, warnings=warnings)

            if window_days < 1 or window_days > MAX_WINDOW_DAYS:
                error = f"Window (days) must be between 1 and {MAX_WINDOW_DAYS}."
                return render_template("schedule.html", schedule=None, error=error, warnings=warnings)

            #read all the drugs the user entered and put them in a list
            drug_ids = request.form.getlist("drug_id[]")
            times_list = request.form.getlist("times_per_day[]")

            required_doses = []

            for idx, (drug_id, times_raw) in enumerate(zip(drug_ids, times_list), start=1):
                drug_id = (drug_id or "").strip()
                times_raw = (times_raw or "").strip()

                # skip empty rows
                if not drug_id and not times_raw:
                    continue

                # skip empty rows
                if not drug_id or not times_raw:
                    error = f"Drug {idx}: both Drug ID and Times per day are required."
                    return render_template("schedule.html", schedule=None, error=error, warnings=warnings)

                # Validate times_per_day
                try:
                    times_per_day = int(times_raw)
                except ValueError:
                    error = f"Drug {idx}: Times per day must be a number."
                    return render_template("schedule.html", schedule=None, error=error, warnings=warnings)

                if times_per_day < 1 or times_per_day > MAX_TIMES_PER_DAY:
                    error = f"Drug {idx}: Times per day must be between 1 and {MAX_TIMES_PER_DAY}."
                    return render_template("schedule.html", schedule=None, error=error, warnings=warnings)

                required_doses.append({
                    "drug_id": drug_id,
                    "times_per_day": times_per_day,
                })

            if not required_doses:
                error = "Please enter at least one drug."
                return render_template("schedule.html", schedule=None, error=error, warnings=warnings)
            

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            # this is just a personal choice, but maybe start at 8:00 am instead of 00:00
            start_dt = datetime.combine(start_date, time(8, 0))
            end_dt = start_dt + timedelta(days=window_days) - timedelta(minutes=1)

            #run the scheduler
            raw_schedule = build_schedule_for_patient(
                patient_id=patient_id,
                required_doses=required_doses,
                start_dt=start_dt,
                end_dt=end_dt,
                slot_minutes=60,   # 1 hour 
            )

            #check if the required doses are scheduled right
            expected_doses = sum(rd["times_per_day"] * window_days for rd in required_doses)
            actual_doses = len(raw_schedule)
            if actual_doses < expected_doses:
                warnings.append(
                    f"Only {actual_doses} of {expected_doses} requested doses could be "
                    "scheduled without violating safety constraints."
                )
            raw_schedule.sort(key=lambda e: e["time"])
            schedule = [
                {
                    "drug_id": entry["drug_id"],
                    "time": entry["time"].strftime("%Y-%m-%d %H:%M"),
                    "quantity": entry["quantity"],   # always 1
                }
                for entry in raw_schedule
            ]

        except Exception as e:
            error = f"Error: {e}"

    return render_template("schedule.html", schedule=schedule, error=error, warnings=warnings)


if __name__ == "__main__":
    app.run(debug=True)
