# TODO:
# Factor out constants;
# Make the json_parser support decimal and negative values;
# The only thing left is compute time in different modes (low, normal, high).

from enum import StrEnum
from json_parser import parse_json


SPEC_FOLDER = "../spec/"

class State(StrEnum):
    VOID    = "",
    WORKING = "working_s",
    STOPPED = "stopped_s",
    INVALID = "invalid_s",
    GAP     = "gap_s"

def main():
    files = ["01_small", "03_gap_20min", "04_invalid_values", "05_long_record", "06_empty", "07_single_point"]
    for filei in range(len(files)):
        files[filei] = SPEC_FOLDER + files[filei] + ".json"
    data_json = open(files[0]).read()
    samples = parse_json(data_json).samples
    stats = collect_stats(samples)
    print_stats(stats)

def is_invalid(sample):
    return (sample.valid == False) or \
           (sample.rpm is None or sample.rpm < 0) or \
           (sample.pressure_mpa is None or sample.pressure_mpa < 0)

# TODO: Better naming
def get_state(sample_current, sample_next):
    if sample_next.t_s - sample_current.t_s > 1.5:
        return State.GAP
    if is_invalid(sample_current):
        return State.INVALID
    elif sample_current.rpm < 50 or sample_current.pressure_mpa < 1:
        return State.STOPPED
    else:
        return State.WORKING

def collect_stats(samples):
    start = None
    last_state = State.VOID
    samples_cnt = len(samples)
    stats = {
        State.WORKING: 0,
        State.STOPPED: 0,
        State.INVALID: 0,
        State.GAP:     0
    }
    for samplei in range(samples_cnt):
        current = samples[samplei]
        nextt = samples[samplei + 1] if samplei < samples_cnt - 1 else None

        # The last sample needs special treatment (probably)
        if nextt is None:
            if last_state == State.VOID or start is None:
                continue
            stats[last_state] += current.t_s - start.t_s
            continue

        if last_state == State.VOID:
            start = current
            last_state = get_state(current, nextt)
            continue

        current_state = get_state(current, nextt)
        if current_state == last_state:
            continue
        stats[last_state] += current.t_s - start.t_s
        start = current
        last_state = current_state
    return stats

def print_stats(stats):
    for state in stats:
        print(f"{state}: {stats[state]}")

if __name__ == "__main__":
    main()

