# src/data_handler.py
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

def _abs_path(base_dir: str, rel_path: str) -> str:
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(base_dir, rel_path)

def read_csv_rows(path: str) -> Optional[List[Dict[str, str]]]:
    if not os.path.exists(path):
        return None
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]

def write_csv_rows(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ('' if r.get(k) is None else r.get(k)) for k in fieldnames})

def load_all(base_dir: str):
    """
    IMPORTANT: base_dir here is expected to be the folder that contains CSVs directly.
    Example: C:/Users/.../Timetable_Final/data  (NOT the project root)
    """
    data_dir = base_dir
    teachers = read_csv_rows(os.path.join(data_dir, 'teachers.csv'))
    subjects = read_csv_rows(os.path.join(data_dir, 'subjects.csv'))
    rooms = read_csv_rows(os.path.join(data_dir, 'rooms.csv'))
    timeslots = read_csv_rows(os.path.join(data_dir, 'timeslots.csv'))
    sections = read_csv_rows(os.path.join(data_dir, 'sections.csv'))
    return teachers, subjects, rooms, timeslots, sections

def save_teachers(base_dir: str, teachers: List[Dict[str,str]]) -> None:
    path = os.path.join(base_dir, 'teachers.csv')
    fieldnames = ['teacher_id','teacher_name','max_classes_per_day']
    write_csv_rows(path, teachers, fieldnames)

def save_subjects(base_dir: str, subjects: List[Dict[str,str]]) -> None:
    path = os.path.join(base_dir, 'subjects.csv')
    fieldnames = ['subject_code','subject_name','teacher_id','hours_per_week','double_period']
    write_csv_rows(path, subjects, fieldnames)

def save_rooms(base_dir: str, rooms: List[Dict[str,str]]) -> None:
    path = os.path.join(base_dir, 'rooms.csv')
    fieldnames = ['room_id','room_type','capacity']
    write_csv_rows(path, rooms, fieldnames)

def save_timeslots(base_dir: str, timeslots: List[Dict[str,str]]) -> None:
    path = os.path.join(base_dir, 'timeslots.csv')
    fieldnames = ['slot_id','day','start_time','end_time']
    write_csv_rows(path, timeslots, fieldnames)

def save_sections(base_dir: str, sections: List[Dict[str,str]]) -> None:
    path = os.path.join(base_dir, 'sections.csv')
    fieldnames = ['section_id','section_name']
    write_csv_rows(path, sections, fieldnames)

# ---------------------------------------------
# ADDED: COMMON GROUP DEFINITIONS FOR AI MODULE
# ---------------------------------------------
def get_common_groups():
    """
    Returns common-section mapping.
    Used by greedy scheduler and OR-Tools.
    """
    return {
        "COMMON-AI": [
            "SEC-AI-ML1",
            "SEC-AI-ML2",
            "SEC-AI",
            "SEC-AI-DS1",
            "SEC-AI-DS2"
        ]
    }

def _is_time(t: str) -> bool:
    try:
        datetime.strptime(t, "%H:%M")
        return True
    except Exception:
        return False

def validate_all(teachers, subjects, rooms, timeslots, sections) -> List[str]:
    errors = []
    if teachers is None:
        errors.append("teachers.csv missing")
    if subjects is None:
        errors.append("subjects.csv missing")
    if rooms is None:
        errors.append("rooms.csv missing")
    if timeslots is None:
        errors.append("timeslots.csv missing")
    if sections is None:
        errors.append("sections.csv missing")
    if errors:
        return errors

    def ids(rows, key):
        return [r.get(key,'').strip() for r in rows]

    t_ids = ids(teachers, 'teacher_id')
    if len(t_ids) != len(set(t_ids)):
        errors.append("duplicate teacher_id in teachers.csv")

    s_codes = ids(subjects, 'subject_code')
    if len(s_codes) != len(set(s_codes)):
        errors.append("duplicate subject_code in subjects.csv")

    r_ids = ids(rooms, 'room_id')
    if len(r_ids) != len(set(r_ids)):
        errors.append("duplicate room_id in rooms.csv")

    slot_ids = ids(timeslots, 'slot_id')
    if len(slot_ids) != len(set(slot_ids)):
        errors.append("duplicate slot_id in timeslots.csv")

    for s in subjects:
        tid = s.get('teacher_id','').strip()
        if tid == '':
            errors.append(f"subject {s.get('subject_code','?')} missing teacher_id")
        elif tid not in t_ids:
            errors.append(f"subject {s.get('subject_code','?')} references unknown teacher_id {tid}")

    for s in subjects:
        try:
            int(s.get('hours_per_week','0'))
        except:
            errors.append(f"subject {s.get('subject_code','?')} has invalid hours_per_week")

    for t in teachers:
        try:
            int(t.get('max_classes_per_day','0'))
        except:
            errors.append(f"teacher {t.get('teacher_id','?')} has invalid max_classes_per_day")

    for r in rooms:
        try:
            int(r.get('capacity','0'))
        except:
            errors.append(f"room {r.get('room_id','?')} has invalid capacity")

    for ts in timeslots:
        st = ts.get('start_time','')
        et = ts.get('end_time','')
        if not _is_time(st) or not _is_time(et):
            errors.append(f"slot {ts.get('slot_id','?')} has bad time format")
        else:
            if datetime.strptime(st,"%H:%M") >= datetime.strptime(et,"%H:%M"):
                errors.append(f"slot {ts.get('slot_id','?')} start_time >= end_time")

    return errors
# data_handler.py
import csv, os
from datetime import datetime
from typing import List, Dict, Optional

def read_csv_rows(path: str) -> Optional[List[Dict[str, str]]]:
    if not os.path.exists(path):
        return None
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]

def write_csv_rows(path: str, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ('' if r.get(k) is None else r.get(k)) for k in fieldnames})

def load_all(base_dir: str):
    data_dir = base_dir
    teachers = read_csv_rows(os.path.join(data_dir, 'teachers.csv'))
    subjects = read_csv_rows(os.path.join(data_dir, 'subjects.csv'))
    rooms = read_csv_rows(os.path.join(data_dir, 'rooms.csv'))
    timeslots = read_csv_rows(os.path.join(data_dir, 'timeslots.csv'))
    sections = read_csv_rows(os.path.join(data_dir, 'sections.csv'))
    return teachers, subjects, rooms, timeslots, sections

def get_common_groups():
    # keep earlier mapping; update if needed
    return {
        "COMMON-AI": [
            "CSE-AI-ML1","CSE-AI-ML2","CSE-AI","CSE-AI-DS1","CSE-AI-DS2"
        ]
    }

def validate_all(teachers, subjects, rooms, timeslots, sections):
    errors = []
    if teachers is None:
        errors.append("teachers.csv missing")
    if subjects is None:
        errors.append("subjects.csv missing")
    if rooms is None:
        errors.append("rooms.csv missing")
    if timeslots is None:
        errors.append("timeslots.csv missing")
    if sections is None:
        errors.append("sections.csv missing")
    if errors:
        return errors
    # basic uniqueness checks
    def ids(rows, key):
        return [r.get(key,'').strip() for r in rows]
    if len(ids(teachers,'teacher_id')) != len(set(ids(teachers,'teacher_id'))):
        errors.append("duplicate teacher_id in teachers.csv")
    if len(ids(subjects,'subject_code')) != len(set(ids(subjects,'subject_code'))):
        errors.append("duplicate subject_code in subjects.csv")
    if len(ids(rooms,'room_id')) != len(set(ids(rooms,'room_id'))):
        errors.append("duplicate room_id in rooms.csv")
    if len(ids(timeslots,'slot_id')) != len(set(ids(timeslots,'slot_id'))):
        errors.append("duplicate slot_id in timeslots.csv")
    # basic formats
    for s in subjects:
        tid = s.get('teacher_id','').strip()
        if tid == '':
            errors.append(f"subject {s.get('subject_code','?')} missing teacher_id")
    return errors
