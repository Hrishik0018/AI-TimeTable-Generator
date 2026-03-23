# src/updater_ai.py
"""
Lightweight AI command parser for common timetable updates.
Parses english-like commands and updates CSV files under base_dir.
Supported:
 - Make <subject-name or code> double period
 - Remove double period for <subject>
 - Set <subject> hours to <N>
 - Assign <subject> to <TID> or to <teacher name>
 - Set <teacher_id> max classes per day to N
 - Set room <ROOM_ID> capacity to N
"""

import os, csv, re
from pathlib import Path

def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def _find_subject_by_name_or_code(subjects, token):
    token_low = token.strip().lower()
    # match code exact first
    for s in subjects:
        if s.get("subject_code","").lower() == token_low:
            return s
    # then approximate match on name
    for s in subjects:
        if token_low in s.get("subject_name","").lower():
            return s
    return None

def _find_teacher_by_id_or_name(teachers, token):
    t_low = token.strip().lower()
    for t in teachers:
        if t.get("teacher_id","").lower() == t_low:
            return t
    for t in teachers:
        if token.strip().lower() in t.get("teacher_name","").lower():
            return t
    return None

def parse_and_apply(command: str, base_dir=".", regen=False, regen_func=None):
    """
    Parse a single command and apply to CSVs in base_dir.
    If regen==True and regen_func provided, it will call regen_func() after modifications.
    Returns (ok:bool, message:str)
    """
    base = Path(base_dir)
    # data folder detection
    data_dir = base / "data" if (base / "data").exists() else base

    try:
        subjects = _load_csv(data_dir / "subjects.csv")
        teachers = _load_csv(data_dir / "teachers.csv")
        rooms = _load_csv(data_dir / "rooms.csv")
    except FileNotFoundError as e:
        return False, f"Missing CSV: {e}"

    cmd = command.strip().lower()

    # patterns
    m = re.match(r".*(make|set)\s+(.+?)\s+double\s+(period|session|class).*", command, flags=re.I)
    if m:
        token = m.group(2)
        subj = _find_subject_by_name_or_code(subjects, token)
        if not subj:
            return False, f"Could not find subject '{token}'"
        subj["double_period"] = "yes"
        _write_csv(data_dir / "subjects.csv", subjects[0].keys(), subjects)
        if regen and callable(regen_func):
            regen_func()
        return True, f"Set {subj.get('subject_code')} as double period."

    m = re.match(r".*(remove|clear)\s+double\s+period\s+for\s+(.+)", command, flags=re.I)
    if m:
        token = m.group(2)
        subj = _find_subject_by_name_or_code(subjects, token)
        if not subj:
            return False, f"Could not find subject '{token}'"
        subj["double_period"] = "no"
        _write_csv(data_dir / "subjects.csv", subjects[0].keys(), subjects)
        if regen and callable(regen_func):
            regen_func()
        return True, f"Removed double period for {subj.get('subject_code')}."

    m = re.match(r".*(set|make)\s+(.+?)\s+hours?\s+(to|=)\s*(\d+).*", command, flags=re.I)
    if m:
        token = m.group(2)
        val = int(m.group(4))
        subj = _find_subject_by_name_or_code(subjects, token)
        if not subj:
            return False, f"Subject '{token}' not found"
        subj["hours_per_week"] = str(val)
        _write_csv(data_dir / "subjects.csv", subjects[0].keys(), subjects)
        if regen and callable(regen_func):
            regen_func()
        return True, f"Set {subj.get('subject_code')} hours to {val}."

    m = re.match(r".*(assign|set)\s+(.+?)\s+to\s+(t\d+|mr\.|ms\.|dr\.).*", command, flags=re.I)
    if m:
        # try code or name then teacher id or name
        token = m.group(2)
        # extract teacher token after 'to'
        after = command.lower().split(" to ",1)[1]
        subj = _find_subject_by_name_or_code(subjects, token)
        if not subj:
            return False, f"Subject '{token}' not found"
        teacher = _find_teacher_by_id_or_name(teachers, after)
        if not teacher:
            return False, f"Teacher '{after}' not found"
        subj["teacher_id"] = teacher["teacher_id"]
        _write_csv(data_dir / "subjects.csv", subjects[0].keys(), subjects)
        if regen and callable(regen_func):
            regen_func()
        return True, f"Assigned {subj.get('subject_code')} to {teacher.get('teacher_id')}."

    # teacher max classes
    m = re.match(r".*(set|limit)\s+(t\d+)\s+max\s+classes\s+per\s+day\s+to\s+(\d+).*", command, flags=re.I)
    if m:
        tid = m.group(2)
        val = m.group(3)
        teacher = _find_teacher_by_id_or_name(teachers, tid)
        if not teacher:
            return False, f"Teacher '{tid}' not found"
        teacher["max_classes_per_day"] = str(val)
        _write_csv(data_dir / "teachers.csv", teachers[0].keys(), teachers)
        if regen and callable(regen_func):
            regen_func()
        return True, f"Set {teacher.get('teacher_id')} max classes per day to {val}."

    # room capacity
    m = re.match(r".*set\s+room\s+([a-zA-Z0-9\- ]+)\s+capacity\s+to\s+(\d+).*", command, flags=re.I)
    if m:
        room_tok = m.group(1).strip()
        cap = m.group(2)
        for r in rooms:
            if r["room_id"].lower() == room_tok.lower():
                r["capacity"] = cap
                _write_csv(data_dir / "rooms.csv", rooms[0].keys(), rooms)
                return True, f"Set room {r['room_id']} capacity to {cap}"
        return False, f"Room '{room_tok}' not found"

    return False, "Command not recognized. Try: 'Make Mathematics double period', 'Set Physics hours to 4', 'Assign TCS-302 to T012', 'Set T012 max classes per day to 3'."
