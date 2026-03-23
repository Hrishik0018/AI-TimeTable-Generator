"""
src/csv_auto_detect.py

Smart CSV detector: accepts a path to an uploaded CSV file, inspects headers and sample rows,
guesses what type(s) of data it contains (teachers, subjects, rooms, timeslots, sections),
and writes appropriate data files into data/ (merging or replacing).
"""

import os, csv
from typing import List, Dict, Tuple
from src import data_handler

TYPE_KEYWORDS = {
    'teachers': {'teacher_id','teacher_name','max_classes_per_day','max_per_day','teacher'},
    'subjects': {'subject_code','subject_name','teacher_id','hours_per_week','double_period','subject'},
    'rooms': {'room_id','room_type','capacity','room'},
    'timeslots': {'slot_id','day','start_time','end_time','timeslot','time'},
    'sections': {'section_id','section_name','section'}
}

def _read_head_rows(path: str, nrows: int = 5):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = []
        for i, r in enumerate(reader):
            if i >= nrows: break
            rows.append({k:v for k,v in r.items()})
        return headers, rows

def _score_type(headers):
    hset = set(h.lower() for h in (headers or []))
    scores = {}
    for t, keys in TYPE_KEYWORDS.items():
        scores[t] = len(hset & keys)
    return scores

def detect_csv_type(path: str):
    headers, _ = _read_head_rows(path, nrows=3)
    scores = _score_type(headers)
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_types

def detect_and_import(uploaded_csv_path: str, base_dir: str, mode: str = 'merge'):
    if not os.path.exists(uploaded_csv_path):
        return False, "Uploaded file not found"

    types = detect_csv_type(uploaded_csv_path)
    if not types:
        return False, "Could not read CSV headers"

    candidates = [t for t,s in types if s > 0]
    if not candidates:
        return False, "Could not infer CSV type from headers"

    with open(uploaded_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]
    headers = [h.lower() for h in (reader.fieldnames or [])]

    def _merge_or_replace(target_path, new_rows, key, mode):
        existing = data_handler.read_csv_rows(target_path) if os.path.exists(target_path) else []
        if mode == 'replace' or not existing:
            return new_rows
        exist_map = {e.get(key): e for e in existing}
        for r in new_rows:
            k = r.get(key)
            if k not in exist_map or not exist_map[k]:
                exist_map[k] = r
            else:
                for field, val in r.items():
                    if val is not None and val != '':
                        exist_map[k][field] = val
        return list(exist_map.values())

    header_set = set(headers)
    if 'subject_code' in header_set or ('teacher_id' in header_set and 'subject_code' in header_set):
        teachers_list, subjects_list = data_handler.subjects_from_teacher_upload(rows)
        if teachers_list:
            tpath = os.path.join(base_dir, 'data', 'teachers.csv')
            merged_teachers = _merge_or_replace(tpath, teachers_list, 'teacher_id', mode)
            data_handler.save_teachers(base_dir, merged_teachers)
        if subjects_list:
            spath = os.path.join(base_dir, 'data', 'subjects.csv')
            merged_subjects = _merge_or_replace(spath, subjects_list, 'subject_code', mode)
            data_handler.save_subjects(base_dir, merged_subjects)
        return True, f"Imported combined teacher/subject CSV: {len(teachers_list)} teachers, {len(subjects_list)} subjects"

    best_type, best_score = detect_csv_type(uploaded_csv_path)[0]

    if best_type == 'teachers':
        mapped = []
        for r in rows:
            tid = r.get('teacher_id') or r.get('id') or r.get('tid') or r.get('teacher')
            tname = r.get('teacher_name') or r.get('teacher') or r.get('name')
            maxc = r.get('max_classes_per_day') or r.get('max_per_day') or r.get('max') or r.get('max_classes')
            mapped.append({'teacher_id': str(tid).strip(), 'teacher_name': str(tname).strip(), 'max_classes_per_day': str(maxc).strip()})
        tpath = os.path.join(base_dir, 'data', 'teachers.csv')
        out = _merge_or_replace(tpath, mapped, 'teacher_id', mode)
        data_handler.save_teachers(base_dir, out)
        return True, f"Imported teachers CSV: {len(mapped)} rows"

    if best_type == 'subjects':
        mapped = []
        for r in rows:
            sc = r.get('subject_code') or r.get('code') or r.get('sub_code') or r.get('subject')
            sname = r.get('subject_name') or r.get('subject') or r.get('sub_name')
            tid = r.get('teacher_id') or r.get('teacher')
            hrs = r.get('hours_per_week') or r.get('hours') or r.get('hrs') or '0'
            dbl = r.get('double_period') or r.get('double') or 'no'
            mapped.append({'subject_code': str(sc).strip(), 'subject_name': str(sname).strip(), 'teacher_id': str(tid).strip(), 'hours_per_week': str(hrs).strip(), 'double_period': ('yes' if str(dbl).strip().lower() in ['yes','true','1','y'] else 'no')})
        spath = os.path.join(base_dir, 'data', 'subjects.csv')
        out = _merge_or_replace(spath, mapped, 'subject_code', mode)
        data_handler.save_subjects(base_dir, out)
        return True, f"Imported subjects CSV: {len(mapped)} rows"

    if best_type == 'rooms':
        mapped = []
        for r in rows:
            rid = r.get('room_id') or r.get('room') or r.get('id')
            rtype = r.get('room_type') or r.get('type') or 'Lecture'
            cap = r.get('capacity') or r.get('cap') or '0'
            mapped.append({'room_id': str(rid).strip(), 'room_type': str(rtype).strip(), 'capacity': str(cap).strip()})
        rpath = os.path.join(base_dir, 'data', 'rooms.csv')
        out = _merge_or_replace(rpath, mapped, 'room_id', mode)
        data_handler.save_rooms(base_dir, out)
        return True, f"Imported rooms CSV: {len(mapped)} rows"

    if best_type == 'timeslots':
        mapped = []
        for r in rows:
            sid = r.get('slot_id') or r.get('slot') or r.get('id')
            day = r.get('day') or r.get('weekday') or ''
            st = r.get('start_time') or r.get('start') or ''
            et = r.get('end_time') or r.get('end') or ''
            mapped.append({'slot_id': str(sid).strip(), 'day': str(day).strip(), 'start_time': str(st).strip(), 'end_time': str(et).strip()})
        p = os.path.join(base_dir, 'data', 'timeslots.csv')
        out = _merge_or_replace(p, mapped, 'slot_id', mode)
        data_handler.save_timeslots(base_dir, out)
        return True, f"Imported timeslots CSV: {len(mapped)} rows"

    if best_type == 'sections':
        mapped = []
        for r in rows:
            sid = r.get('section_id') or r.get('section') or r.get('id')
            sname = r.get('section_name') or r.get('name') or ''
            mapped.append({'section_id': str(sid).strip(), 'section_name': str(sname).strip()})
        p = os.path.join(base_dir, 'data', 'sections.csv')
        out = _merge_or_replace(p, mapped, 'section_id', mode)
        data_handler.save_sections(base_dir, out)
        return True, f"Imported sections CSV: {len(mapped)} rows"

    return False, "No matching type detected for CSV"
