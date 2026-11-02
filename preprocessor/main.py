# TODO:
# Factor out constants;
# Compute time in different modes (low, normal, high)--basically split WORKING state into 3 and that's it (I hope);
# Compute span;
# Process format errors;
# Generate result.json (so it matches the "expected_results.json" file); 
# Create tests;
# Add type hints.

from enum import StrEnum
from json_parser import parse_json


SPEC_FOLDER = "../spec/"

# TODO: Maybe use separate enums for "state" stats and "dervied" stats and then combine them (and keep the State as well)

# TODO: I completely forgot to use this enum...
class Stat(StrEnum):
    SPAN    = "span_s"
    WORKING = "working_s"
    STOPPED = "stopped_s"
    GAP     = "gap_s"
    INVALID = "invalid_s"
    UNKNOWN = "unknown_s"
    LOW     = "low"
    NORMAL  = "normal"
    HIGH    = "high"

# TODO: This enum doens't need to be string-based anymore (?)
class State(StrEnum):
    VOID    = ""
    STOPPED = "stopped_s"
    LOW     = "low_s"
    NORMAL  = "normal_s"
    HIGH    = "high_s"
    INVALID = "invalid_s"
    GAP     = "gap_s"

def main():
    files = ["01_small", "02_boundaries", "03_gap_20min", "04_invalid_values", "05_long_record", "06_empty", "07_single_point", "08_missing_rpm", "09_wrong_type", "10_duplicate_time"]
    for filei in range(len(files)):
        files[filei] = SPEC_FOLDER + files[filei] + ".json"
    data_json = open(files[4]).read()
    samples = parse_json(data_json).samples

    state_stats = collect_state_stats(samples)
    derived_stats = get_derived_stats(state_stats)
    results = form_results(state_stats, derived_stats)
    print(results)

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
    elif 1 <= sample_current.pressure_mpa < 5:
        return State.LOW
    elif 5 <= sample_current.pressure_mpa < 10:
        return State.NORMAL
    else:
        return State.HIGH

# TODO: Better naming
# NOTE: This function collects intervals in each of the states
def collect_state_stats(samples):
    start = None
    last_state = State.VOID
    samples_cnt = len(samples)
    stats = {
        State.STOPPED: 0,
        State.LOW:     0,
        State.NORMAL:  0,
        State.HIGH:    0,
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

# TODO: Poor design
def get_derived_stats(state_stats):
    results = dict()
    unknown_s = ("unknown_s", State.GAP, State.INVALID)
    working_s = ("working_s", State.LOW, State.NORMAL, State.HIGH)
    span_s    = ("span_s", State.STOPPED) # + unknown_s + working_s
    derived_stats = (unknown_s, working_s, span_s)
    for stat in derived_stats:
        stat_name = stat[0]
        results[stat_name] = 0
        for state in range(1, len(stat)):
            results[stat_name] += state_stats[stat[state]]
    results[span_s[0]] += results[unknown_s[0]]
    results[span_s[0]] += results[working_s[0]]
    return results

#{
#    "status": "ok",
#    "sample_count": 13,
#    "span_s": 12,
#    "working_s": 9,
#    "stopped_s": 3,
#    "gap_s": 0,
#    "invalid_s": 0,
#    "unknown_s": 0,
#    "modes_s": {
#        "low": 3,
#        "normal": 3,
#        "high": 3
#}

# TODO: Better naming;
#       It's really bad that the "collect_state_stats" func returns dict whose values are enum fields while the "get_derived_stats" func uses strings instead.
#       Result must be as shown above.
def form_results(state_stats, derived_stats):
    result = dict()
    for stat, value in state_stats.items():
        result[str(stat)] = value
    for stat, value in derived_stats.items():
        result[stat] = value
    return result

def print_stats(stats):
    for state in stats:
        print(f"{state}: {stats[state]}")

if __name__ == "__main__":
    main()

