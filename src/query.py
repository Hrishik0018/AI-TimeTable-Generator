def teacher_timetable(timetable_rows, teacher_id):
    return [r for r in timetable_rows if r.get('teacher_id') == teacher_id]

def section_timetable(timetable_rows, section_id):
    return [r for r in timetable_rows if r.get('section_id') == section_id]
