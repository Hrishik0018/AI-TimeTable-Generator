import csv
import os

try:
    import pandas as pd
except Exception:
    pd = None


def save_csv(rows, filename="timetable.csv", base_dir=None):
    base = base_dir or os.getcwd()
    out = os.path.join(base, filename)
    if not rows:
        return out
    fieldnames = list(rows[0].keys())
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def _load_timeslots(base_dir):
    """
    Load timeslots from data/timeslots.csv if available.
    Returns list of dicts or [].
    """
    path = os.path.join(base_dir, "data", "timeslots.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _day_order(d):
    order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    try:
        return order.index(d.lower())
    except Exception:
        return 100


def save_excel_flat(rows, filename="timetable_flat.xlsx", base_dir=None):
    """
    Simple table export (one sheet, all rows).
    Kept in case you still want the flat style.
    """
    if pd is None:
        raise RuntimeError("pandas not installed")
    base = base_dir or os.getcwd()
    out = os.path.join(base, filename)
    df = pd.DataFrame(rows)
    df.to_excel(out, index=False)
    return out


def save_excel_grid(rows, filename="timetable_grid.xlsx", base_dir=None):
    """
    Export timetable in CLASSIC GRID FORMAT:

    - One sheet per SECTION
    - Rows = Days (Monday..Friday)
    - Columns = Time slots (e.g. 09:00-10:00)
    - Cell = "Subject (T01) @R101"
    """
    if pd is None:
        raise RuntimeError("pandas not installed")

    base = base_dir or os.getcwd()
    out = os.path.join(base, filename)
    if not rows:
        # still create empty file
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            pass
        return out

    # Try to get slot structure from timeslots.csv, otherwise infer from timetable rows
    timeslots = _load_timeslots(base)
    if timeslots:
        # timeslots.csv exists – use its ordering
        # unique days and slots
        days = sorted({ts["day"] for ts in timeslots}, key=_day_order)
        slot_labels = []
        for ts in sorted(timeslots, key=lambda t: (_day_order(t["day"]), t["start_time"])):
            label = f"{ts['start_time']}-{ts['end_time']}"
            if label not in slot_labels:
                slot_labels.append(label)
    else:
        # infer from rows
        days = sorted({r["day"] for r in rows}, key=_day_order)
        slot_labels = []
        for r in rows:
            label = f"{r['start_time']}-{r['end_time']}"
            if label not in slot_labels:
                slot_labels.append(label)
        slot_labels.sort()

    # Group rows by section_id
    section_map = {}
    for r in rows:
        sid = r.get("section_id", "UNKNOWN")
        section_map.setdefault(sid, []).append(r)

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for section_id, srows in section_map.items():
            # Build grid: index = days, columns = slot_labels
            grid_data = []
            for day in days:
                row_cells = []
                for slabel in slot_labels:
                    # slabel = "start-end"
                    start, end = slabel.split("-")
                    # find all entries for this section, day, slot
                    matches = [
                        r
                        for r in srows
                        if r["day"] == day
                        and r["start_time"] == start
                        and r["end_time"] == end
                    ]
                    if not matches:
                        row_cells.append("")
                    else:
                        # join multiple if any (should be 1)
                        texts = []
                        for m in matches:
                            subj = m.get("subject_name", "")
                            tid = m.get("teacher_id", "")
                            room = m.get("room_id", "")
                            # format: Subject (TID) @ROOM
                            part = f"{subj}"
                            if tid:
                                part += f" ({tid})"
                            if room:
                                part += f" @{room}"
                            texts.append(part)
                        row_cells.append(" | ".join(texts))
                grid_data.append(row_cells)
            df = pd.DataFrame(grid_data, index=days, columns=slot_labels)

            # sheet name: prefer section_name if available
            any_row = srows[0]
            sname = any_row.get("section_name") or section_id
            sheet_name = str(sname)[:31]  # Excel max sheet name length
            df.to_excel(writer, sheet_name=sheet_name)

    return out
