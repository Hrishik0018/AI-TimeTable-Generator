import os, csv

teachers = [
    {"teacher_id":"T01","teacher_name":"Dr. Mehta","max_classes_per_day":"4"},
    {"teacher_id":"T02","teacher_name":"Ms. Roy","max_classes_per_day":"4"},
    {"teacher_id":"T03","teacher_name":"Mr. Khan","max_classes_per_day":"4"},
    {"teacher_id":"T04","teacher_name":"Ms. Sharma","max_classes_per_day":"4"},
    {"teacher_id":"T05","teacher_name":"Mr. Verma","max_classes_per_day":"4"},
    {"teacher_id":"T06","teacher_name":"Ms. Iyer","max_classes_per_day":"4"}
]

subjects = [
    {"subject_code":"S01","subject_name":"Mathematics","teacher_id":"T01","hours_per_week":"5","double_period":"no"},
    {"subject_code":"S02","subject_name":"Physics","teacher_id":"T02","hours_per_week":"4","double_period":"no"},
    {"subject_code":"S03","subject_name":"Computer Science","teacher_id":"T03","hours_per_week":"4","double_period":"yes"},
    {"subject_code":"S04","subject_name":"Chemistry","teacher_id":"T04","hours_per_week":"4","double_period":"no"},
    {"subject_code":"S05","subject_name":"Biology","teacher_id":"T05","hours_per_week":"3","double_period":"no"},
    {"subject_code":"S06","subject_name":"English","teacher_id":"T06","hours_per_week":"3","double_period":"no"}
]

rooms = [
    {"room_id":"R101","room_type":"Lecture","capacity":"80"},
    {"room_id":"R102","room_type":"Lecture","capacity":"80"},
    {"room_id":"R103","room_type":"Lecture","capacity":"80"},
    {"room_id":"R104","room_type":"Lecture","capacity":"80"}
]

timeslots = [
    {"slot_id":"TS01","day":"Monday","start_time":"09:00","end_time":"10:00"},
    {"slot_id":"TS02","day":"Monday","start_time":"10:00","end_time":"11:00"},
    {"slot_id":"TS03","day":"Monday","start_time":"11:00","end_time":"12:00"},
    {"slot_id":"TS04","day":"Monday","start_time":"12:00","end_time":"13:00"},
    {"slot_id":"TS05","day":"Monday","start_time":"13:00","end_time":"14:00"},
    {"slot_id":"TS06","day":"Tuesday","start_time":"09:00","end_time":"10:00"},
    {"slot_id":"TS07","day":"Tuesday","start_time":"10:00","end_time":"11:00"},
    {"slot_id":"TS08","day":"Tuesday","start_time":"11:00","end_time":"12:00"},
    {"slot_id":"TS09","day":"Tuesday","start_time":"12:00","end_time":"13:00"},
    {"slot_id":"TS10","day":"Tuesday","start_time":"13:00","end_time":"14:00"},
    {"slot_id":"TS11","day":"Wednesday","start_time":"09:00","end_time":"10:00"},
    {"slot_id":"TS12","day":"Wednesday","start_time":"10:00","end_time":"11:00"},
    {"slot_id":"TS13","day":"Wednesday","start_time":"11:00","end_time":"12:00"},
    {"slot_id":"TS14","day":"Wednesday","start_time":"12:00","end_time":"13:00"},
    {"slot_id":"TS15","day":"Wednesday","start_time":"13:00","end_time":"14:00"},
    {"slot_id":"TS16","day":"Thursday","start_time":"09:00","end_time":"10:00"},
    {"slot_id":"TS17","day":"Thursday","start_time":"10:00","end_time":"11:00"},
    {"slot_id":"TS18","day":"Thursday","start_time":"11:00","end_time":"12:00"},
    {"slot_id":"TS19","day":"Thursday","start_time":"12:00","end_time":"13:00"},
    {"slot_id":"TS20","day":"Thursday","start_time":"13:00","end_time":"14:00"},
    {"slot_id":"TS21","day":"Friday","start_time":"09:00","end_time":"10:00"},
    {"slot_id":"TS22","day":"Friday","start_time":"10:00","end_time":"11:00"},
    {"slot_id":"TS23","day":"Friday","start_time":"11:00","end_time":"12:00"},
    {"slot_id":"TS24","day":"Friday","start_time":"12:00","end_time":"13:00"},
    {"slot_id":"TS25","day":"Friday","start_time":"13:00","end_time":"14:00"}
]

sections = [
    {"section_id":"SEC01","section_name":"Section A"},
    {"section_id":"SEC02","section_name":"Section B"},
    {"section_id":"SEC03","section_name":"Section C"}
]

def write_csv(filename, rows, fieldnames):
    with open(filename,"w",newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main():
    os.makedirs("data", exist_ok=True)
    write_csv(os.path.join("data","teachers.csv"), teachers, ["teacher_id","teacher_name","max_classes_per_day"])
    write_csv(os.path.join("data","subjects.csv"), subjects, ["subject_code","subject_name","teacher_id","hours_per_week","double_period"])
    write_csv(os.path.join("data","rooms.csv"), rooms, ["room_id","room_type","capacity"])
    write_csv(os.path.join("data","timeslots.csv"), timeslots, ["slot_id","day","start_time","end_time"])
    write_csv(os.path.join("data","sections.csv"), sections, ["section_id","section_name"])
    print("Sample CSV files created in data/ directory.")

if __name__=="__main__":
    main()
