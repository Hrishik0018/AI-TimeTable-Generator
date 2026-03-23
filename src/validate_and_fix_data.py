# validate_and_fix_data.py
# Usage: python validate_and_fix_data.py --data "D:/Timetable_Final/data"
import argparse, os, csv, shutil
from datetime import datetime

def read_csv(path):
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames})

def backup(path):
    if os.path.exists(path):
        bak = path + ".bak"
        shutil.copy(path, bak)
        print("  backup ->", bak)

def try_int(s, default=3):
    try:
        return int(float(str(s).strip()))
    except:
        return default

def is_time_ok(t):
    try:
        if not t or ":" not in t: return False
        hh,mm = t.split(":")[:2]
        hh=int(hh); mm=int(mm)
        return 0<=hh<=23 and 0<=mm<=59
    except: return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="../data", help="data dir path")
    a = p.parse_args()
    data = os.path.abspath(a.data)
    print("Data folder:", data)
    expected = {
        "subjects.csv": ["subject_code","subject_name","teacher_id","hours_per_week","double_period"],
        "teachers.csv": ["teacher_id","teacher_name","max_classes_per_day"],
        "section_subject_map.csv": ["section_id","subject_code"],
        "sections.csv": ["section_id","section_name"],
        "timeslots.csv": ["slot_id","day","start_time","end_time"],
        "rooms.csv": ["room_id","room_type","capacity"],
        "teacher_subject_map.csv": ["teacher_id","subject_code"]
    }

    # load
    tables={}
    for name in expected:
        path=os.path.join(data,name)
        rows=read_csv(path)
        print(f"\n{name}: {'FOUND' if rows is not None else 'MISSING'}", end="")
        if rows is not None:
            print(f"  rows={len(rows)}")
            tables[name]=rows
        else:
            print()

    errors=[]
    # Quick checks
    # teachers
    teachers = tables.get("teachers.csv", [])
    teacher_ids = set()
    for t in teachers:
        tid = (t.get("teacher_id") or "").strip()
        if not tid:
            errors.append("teachers.csv: a row with empty teacher_id")
        teacher_ids.add(tid)

    # subjects
    subjects = tables.get("subjects.csv", [])
    subject_codes=set()
    missing_teacher_subjects=[]
    bad_hours=[]
    for s in subjects:
        code = (s.get("subject_code") or "").strip()
        subject_codes.add(code)
        tid = (s.get("teacher_id") or "").strip()
        if tid=="":
            missing_teacher_subjects.append(code)
        hours = s.get("hours_per_week","")
        try:
            int(float(str(hours).strip()))
        except:
            bad_hours.append(code)

    if missing_teacher_subjects:
        print("\nSubjects missing teacher_id:", missing_teacher_subjects)
    if bad_hours:
        print("\nSubjects with invalid hours_per_week (will be set to default 3):", bad_hours)

    # section_subject_map validity
    ssm = tables.get("section_subject_map.csv", [])
    bad_ssm=[]
    for r in ssm:
        sc = (r.get("subject_code") or "").strip()
        if sc not in subject_codes:
            bad_ssm.append(r)
    if bad_ssm:
        print(f"\nsection_subject_map.csv: {len(bad_ssm)} rows reference unknown subject_code (sample):")
        for i,r in enumerate(bad_ssm[:10]):
            print(" ", i+1, r)
        print("  --> These must match subject_code in subjects.csv exactly.")

    # teacher_subject_map validity
    tmap = tables.get("teacher_subject_map.csv", [])
    bad_tmap=[]
    for r in tmap:
        tid=(r.get("teacher_id") or "").strip()
        sc=(r.get("subject_code") or "").strip()
        if tid not in teacher_ids:
            bad_tmap.append(("missing_teacher", r))
        if sc not in subject_codes:
            bad_tmap.append(("missing_subject", r))
    if bad_tmap:
        print(f"\nteacher_subject_map.csv: {len(bad_tmap)} inconsistent rows (sample):")
        for i,(t,r) in enumerate(bad_tmap[:10]):
            print(" ",i+1,t,r)

    # timeslots validity
    times = tables.get("timeslots.csv", [])
    bad_slots=[]
    for r in times:
        st = r.get("start_time","")
        et = r.get("end_time","")
        sid = r.get("slot_id","")
        if not (is_time_ok(st) and is_time_ok(et)):
            bad_slots.append((sid,st,et))
    if bad_slots:
        print("\ntimeslots.csv: bad times (sample):")
        for b in bad_slots[:10]:
            print(" ",b)
        errors.append("timeslots.csv has malformed times - fix start_time/end_time to HH:MM")

    # rooms capacity numeric
    rooms = tables.get("rooms.csv", [])
    bad_rooms=[]
    for r in rooms:
        cap = r.get("capacity","")
        try:
            int(float(str(cap)))
        except:
            bad_rooms.append(r.get("room_id",""))
    if bad_rooms:
        print("\nrooms.csv: rooms with non-numeric capacity:", bad_rooms)

    # DETAILED RECOMMENDATIONS & automatic conservative fixes
    print("\n--- Summary & Conservative Fixes to be written as *_fixed.csv ---")
    fixes_made = {}
    # make backups and write fixed versions
    for name, rows in tables.items():
        path = os.path.join(data, name)
        backup(path)
        fixed = []
        # normalize keys and values
        for r in rows:
            nr = dict(r)  # shallow copy
            # trim all fields
            for k,v in list(nr.items()):
                if isinstance(v,str):
                    nr[k] = v.strip()
            # specific fixes:
            if name=="subjects.csv":
                # normalize subject_code uppercase
                if "subject_code" in nr:
                    nr["subject_code"] = nr.get("subject_code","").strip().upper()
                # ensure hours numeric
                if "hours_per_week" in nr:
                    try:
                        nr["hours_per_week"] = str(int(float(nr.get("hours_per_week","").strip()))) if nr.get("hours_per_week","").strip()!="" else "3"
                    except:
                        nr["hours_per_week"] = "3"
                else:
                    nr["hours_per_week"] = "3"
                # ensure double_period normalized
                if "double_period" in nr:
                    v = nr.get("double_period","").strip().lower()
                    if v in ("yes","y","1","true"):
                        nr["double_period"]="yes"
                    else:
                        nr["double_period"]="no"
                else:
                    nr["double_period"]="no"
                # teacher id default to TBD if missing (conservative)
                if nr.get("teacher_id","").strip()=="":
                    nr["teacher_id"] = "TBD"
            if name=="teachers.csv":
                if "teacher_id" in nr:
                    nr["teacher_id"] = nr.get("teacher_id","").strip()
                if "max_classes_per_day" in nr:
                    try:
                        nr["max_classes_per_day"] = str(int(float(nr.get("max_classes_per_day","").strip()))) if nr.get("max_classes_per_day","").strip()!="" else "4"
                    except:
                        nr["max_classes_per_day"] = "4"
            if name=="rooms.csv":
                if "room_id" in nr:
                    nr["room_id"] = nr.get("room_id","").strip()
                if "capacity" in nr:
                    try:
                        nr["capacity"] = str(int(float(nr.get("capacity","").strip())))
                    except:
                        nr["capacity"] = "30"
                else:
                    nr["capacity"] = "30"
                if "room_type" not in nr:
                    nr["room_type"] = ""
            if name=="timeslots.csv":
                if "slot_id" in nr:
                    nr["slot_id"] = nr.get("slot_id","").strip()
                if "start_time" in nr:
                    st = nr.get("start_time","")
                    if not is_time_ok(st):
                        # try to normalize common patterns "8:00-8:55" or "0800"
                        s = st.strip()
                        if "-" in s:
                            s = s.split("-")[0]
                        if ":" not in s and len(s)>=3:
                            s = s[:-2]+":"+s[-2:]
                        nr["start_time"] = s
                    # leave as-is otherwise
                if "end_time" in nr:
                    et = nr.get("end_time","")
                    if not is_time_ok(et):
                        s = et.strip()
                        if "-" in s:
                            s = s.split("-")[-1]
                        if ":" not in s and len(s)>=3:
                            s = s[:-2]+":"+s[-2:]
                        nr["end_time"] = s
            fixed.append(nr)
        # derive fieldnames (keep original order where possible)
        fieldnames = list(rows[0].keys()) if rows else []
        fixed_path = os.path.join(data, name.replace(".csv","") + "_fixed.csv")
        write_csv(fixed_path, fixed, fieldnames if fieldnames else (list(fixed[0].keys()) if fixed else []))
        fixes_made[name] = fixed_path
        print("Wrote fixed:", fixed_path)

    print("\nFiles fixed (conservative). Next steps:")
    print(" 1) Inspect the *_fixed.csv files in your data folder and confirm changes (especially subjects.csv teacher_id 'TBD' entries).")
    print(" 2) If you approve, rename *_fixed.csv -> original name (or replace) and run the UI again.")
    print(" 3) If you want, paste the console output here and I will propose specific teacher assignments for 'TBD' subjects (I can attempt fuzzy matching by teacher name).")
    print(" 4) After fixing CSVs, run the UI -> Generate Timetable (OR-Tools).")

if __name__ == "__main__":
    main()
