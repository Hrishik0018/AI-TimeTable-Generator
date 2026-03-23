# scheduler_ortools.py
# OR-Tools CP-SAT scheduler (updated: practical auto double-period,
# theory double-period only when user sets, same-room double slots)

from ortools.sat.python import cp_model
import csv, os, sys
from collections import defaultdict


def _read_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate(base_dir="."):
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        print("[ORTools] data folder not found:", data_dir)
        return []

    # Load CSVs
    try:
        sections = _read_csv(os.path.join(data_dir, "sections.csv"))
        section_subject_map = _read_csv(os.path.join(data_dir, "section_subject_map.csv"))
        subjects = _read_csv(os.path.join(data_dir, "subjects.csv"))
        teachers = _read_csv(os.path.join(data_dir, "teachers.csv"))
        rooms = _read_csv(os.path.join(data_dir, "rooms.csv"))
        timeslots = _read_csv(os.path.join(data_dir, "timeslots.csv"))
    except Exception as e:
        print("[ORTools] CSV read error:", e)
        return []

    print("[ORTools] Loaded CSVs:", len(sections), len(subjects), len(teachers), len(rooms), len(timeslots))

    # Mappings
    sections_by_id = {s["section_id"]: s for s in sections}
    subjects_by_code = {s["subject_code"]: s for s in subjects}
    teacher_by_id = {t["teacher_id"]: t for t in teachers}
    all_rooms = [r["room_id"] for r in rooms]

    # Timeslot ordering
    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2,
                 "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}

    timeslots_list = sorted(
        [(ts["slot_id"], ts["day"], ts["start_time"], ts["end_time"]) for ts in timeslots],
        key=lambda x: (day_order.get(x[1], 99), x[2])
    )

    slot_ids = [s[0] for s in timeslots_list]
    slots_by_day = defaultdict(list)
    for sid, d, st, et in timeslots_list:
        slots_by_day[d].append(sid)

    # section → subjects
    sec_to_subjects = defaultdict(list)
    for r in section_subject_map:
        sec_to_subjects[r["section_id"]].append(r["subject_code"])

    # hours + lab detect + double-period flags
    required_slots = {}
    is_lab = {}
    double_period_flag = {}

    for s in subjects:
        code = s["subject_code"].strip()

        # hours
        try:
            h = int(float(s.get("hours_per_week", "1")))
            if h <= 0:
                h = 1
        except:
            h = 1
        required_slots[code] = h

        # lab check
        name = s.get("subject_name", "").lower()
        is_lab[code] = ("lab" in name) or code.upper().startswith("PCS")

        # user double-period flag from CSV
        user_dp = s.get("double_period", "").strip().lower() == "yes"

        # auto practical = endswith P
        auto_practical = code.endswith("P")

        # FINAL RULE:
        # practical → always double
        # theory → only if user double_period=yes
        if auto_practical:
            double_period_flag[code] = True
        else:
            double_period_flag[code] = user_dp

    # Model
    model = cp_model.CpModel()

    # Decision variables
    x = {}
    for sec in sec_to_subjects:
        for sub in sec_to_subjects[sec]:

            lab_pref = is_lab.get(sub, False)
            allowed_rooms = []

            for r in rooms:
                t = r["room_type"].lower()
                rid = r["room_id"].lower()
                if lab_pref and ("lab" in t or "lab" in rid):
                    allowed_rooms.append(r["room_id"])

            if not allowed_rooms:
                allowed_rooms = all_rooms.copy()

            for sid in slot_ids:
                for room in allowed_rooms:
                    x[(sec, sub, sid, room)] = model.NewBoolVar(f"x_{sec}_{sub}_{sid}_{room}")

    # assign_count
    assign_count = {}
    for sec in sec_to_subjects:
        for sub in sec_to_subjects[sec]:
            ub = required_slots[sub]
            v = model.NewIntVar(0, ub, f"count_{sec}_{sub}")
            assign_count[(sec, sub)] = v

            model.Add(v == sum(
                x[(sec, sub, sid, room)]
                for sid in slot_ids
                for room in all_rooms
                if (sec, sub, sid, room) in x
            ))

    # exact hours
    for (sec, sub), v in assign_count.items():
        model.Add(v == required_slots[sub])

    # SECTION clash
    for sec in sec_to_subjects:
        for sid in slot_ids:
            model.Add(sum(
                x[(sec, sub, sid, room)]
                for sub in sec_to_subjects[sec]
                for room in all_rooms
                if (sec, sub, sid, room) in x
            ) <= 1)

    # ROOM clash
    for room in all_rooms:
        for sid in slot_ids:
            model.Add(sum(
                x[(sec, sub, sid, room)]
                for sec in sec_to_subjects
                for sub in sec_to_subjects[sec]
                if (sec, sub, sid, room) in x
            ) <= 1)

    # TEACHER clash
    subject_teacher = {s["subject_code"]: s.get("teacher_id", "") for s in subjects}

    for t_id in teacher_by_id:
        for sid in slot_ids:
            model.Add(sum(
                x[(sec, sub, sid, room)]
                for sec in sec_to_subjects
                for sub in sec_to_subjects[sec]
                if subject_teacher.get(sub, "") == t_id
                for room in all_rooms
                if (sec, sub, sid, room) in x
            ) <= 1)

    # ---------------------------------------------------------
    #  DOUBLE PERIOD (BACK-TO-BACK + SAME ROOM)
    # ---------------------------------------------------------
    for sec in sec_to_subjects:
        for sub in sec_to_subjects[sec]:

            if not double_period_flag.get(sub, False):
                continue

            req = required_slots[sub]
            required_pairs = req // 2
            pair_vars = []

            for day, sids in slots_by_day.items():
                for i in range(len(sids) - 1):
                    s1 = sids[i]
                    s2 = sids[i + 1]

                    # b1: sub assigned at s1
                    b1 = model.NewBoolVar(f"DP_b1_{sec}_{sub}_{s1}")
                    model.Add(sum(x[(sec, sub, s1, r)]
                                  for r in all_rooms if (sec, sub, s1, r) in x) >= 1).OnlyEnforceIf(b1)
                    model.Add(sum(x[(sec, sub, s1, r)]
                                  for r in all_rooms if (sec, sub, s1, r) in x) == 0).OnlyEnforceIf(b1.Not())

                    # b2: sub assigned at s2
                    b2 = model.NewBoolVar(f"DP_b2_{sec}_{sub}_{s2}")
                    model.Add(sum(x[(sec, sub, s2, r)]
                                  for r in all_rooms if (sec, sub, s2, r) in x) >= 1).OnlyEnforceIf(b2)
                    model.Add(sum(x[(sec, sub, s2, r)]
                                  for r in all_rooms if (sec, sub, s2, r) in x) == 0).OnlyEnforceIf(b2.Not())

                    # y = consecutive block
                    y = model.NewBoolVar(f"DP_{sec}_{sub}_{s1}_{s2}")
                    model.Add(y <= b1)
                    model.Add(y <= b2)
                    model.Add(y >= b1 + b2 - 1)

                    # SAME ROOM requirement
                    model.Add(
                        sum(x[(sec, sub, s1, r)] for r in all_rooms if (sec, sub, s1, r) in x)
                        ==
                        sum(x[(sec, sub, s2, r)] for r in all_rooms if (sec, sub, s2, r) in x)
                    ).OnlyEnforceIf(y)

                    pair_vars.append(y)

            model.Add(sum(pair_vars) == required_pairs)

    # Objective
    model.Maximize(1000 * sum(assign_count.values()))

    # Solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = max(1, os.cpu_count() or 1)

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("[ORTools] No feasible solution")
        return []

    # Extract rows
    rows = []
    for sec in sec_to_subjects:
        for sub in sec_to_subjects[sec]:

            info = subjects_by_code.get(sub, {})
            t_id = info.get("teacher_id", "")
            t_name = teacher_by_id.get(t_id, {}).get("teacher_name", "")

            for sid, day, st, et in timeslots_list:
                for room in all_rooms:
                    key = (sec, sub, sid, room)
                    if key in x and solver.Value(x[key]) == 1:
                        rows.append({
                            "section_id": sec,
                            "section_name": sections_by_id.get(sec, {}).get("section_name", sec),
                            "subject_code": sub,
                            "subject_name": info.get("subject_name", sub),
                            "teacher_id": t_id,
                            "teacher_name": t_name,
                            "room_id": room,
                            "slot_id": sid,
                            "day": day,
                            "start_time": st,
                            "end_time": et
                        })

    # Write timetable.csv
    out = os.path.join(data_dir, "timetable.csv")
    if rows:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)

        print("[ORTools] timetable.csv written:", out)
    else:
        print("[ORTools] No rows produced")

    return rows


if __name__ == "__main__":
    base = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath("..")
    print("[ORTools] Running with base:", base)
    r = generate(base)
    print("[ORTools] Done. Rows:", len(r))
