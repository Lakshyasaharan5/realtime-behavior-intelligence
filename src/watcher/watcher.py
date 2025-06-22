import subprocess
import time
from datetime import datetime
import re
import json
import queue
from config.config import NETTOP_DELAY

def run_nettop_command():
    result = subprocess.run(
        ["nettop", "-P", "-x", "-L", "2", "-d", "-s", str(NETTOP_DELAY), "-J", "bytes_in,bytes_out"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return result.stdout

def parse_nettop_output(nettop_output):
    samples = re.split(r',bytes_in,bytes_out,', nettop_output)
    if len(samples) < 3:
        print("Not enough samples found.")
        return

    second_sample = samples[2]
    output = {}

    for line in second_sample.strip().splitlines():
        parts = line.strip().split(',')
        if len(parts) != 4:
            continue

        proc = parts[0]
        try:
            # Extract PID (the part after the last dot)
            pid = int(proc.rsplit('.', 1)[-1])
            in_bytes = int(parts[1])
            out_bytes = int(parts[2])
        except ValueError:
            continue

        # Filter out system processes by PID
        if pid < 1000:
            continue
        
        # Removes pid from name. 'Slack.67532' will convert to 'Slack'
        name_without_pid = proc.rsplit('.', 1)[0]

        # Aggregate data if process name already exists
        if in_bytes > 0 or out_bytes > 0:
            if name_without_pid in output:
                output[name_without_pid]["in"] += in_bytes
                output[name_without_pid]["out"] += out_bytes
            else:
                output[name_without_pid] = {
                    "in": in_bytes,
                    "out": out_bytes
                }

    return output    # json.dumps(output, indent=2)

def watcher_thread_func(q: queue.Queue):
   while True:
        current_timestamp = datetime.now()
        nettop_output = run_nettop_command()
        result = parse_nettop_output(nettop_output)
        q.put((current_timestamp, result))

   
