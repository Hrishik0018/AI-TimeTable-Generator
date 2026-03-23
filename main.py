from src import data_handler, scheduler_ortools, exporter
import os, sys

ROOT = os.path.abspath(os.path.dirname(__file__))
BASE = os.path.join(ROOT, "data")===


def run_all():
    teachers, subjects, rooms, timeslots, sections = data_handler.load_all(BASE)
    errs = data_handler.validate_all(teachers, subjects, rooms, timeslots, sections)
    if errs:
        print("Validation errors:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print("Data validated. Running OR-Tools scheduler...")
    rows = scheduler_ortools.generate(BASE, time_limit_seconds=30)
    if not rows:
        print("No feasible timetable found. Try relaxing constraints.")
        sys.exit(1)
    exporter.save_csv(rows, filename='timetable.csv', base_dir=BASE)
    try:
        exporter.save_excel(rows, filename='timetable.xlsx', base_dir=BASE)
    except Exception:
        print("pandas not installed - excel export skipped")
    print("Timetable generated: timetable.csv")

if __name__ == "__main__":
    run_all()
