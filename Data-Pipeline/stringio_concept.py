import io 
import os 
from datetime import datetime

def parse_file(iostring):
    lines = [line.strip() for line in iostring if line.strip()]
    if not lines:
        return []
    
    headers = [h.strip() for h in lines[0].split(",")]
    data = []
    for line in lines[1:]:
        fields = [f.strip() for f in line.split(",")]
        if len(fields) < len(headers):
            fields.extend([""] * (len(headers) - len(fields)))
        row = dict(zip(headers. fields))
        data.append(row)
    return data

def earned_more_Than_30k(data_struct):
    count = 0
    for row in data_struct:
        try:
            salary = float(row.get("salary", "").replace(",",""))
            if salary > 3000:
                count += 1
        except ValueError:
            continue
    return str(count)

def held_job_longest_in_day(data_struct):
    