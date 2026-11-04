# TODO:
# Factor out constants;
# Create tests;
# Add type hints.

from enum import Enum, StrEnum
from json_parser import parse_json


SPEC_FOLDER = "../spec/"


class BaseStat(StrEnum):
    STOPPED = "stopped_s"
    LOW     = "low"
    NORMAL  = "normal"
    HIGH    = "high"
    INVALID = "invalid_s"
    GAP     = "gap_s"


class DerivedStat(StrEnum):
    SPAN    = "span_s"
    WORKING = "working_s"
    UNKNOWN = "unknown_s"


class State(Enum):
    VOID    = 0
    STOPPED = 1
    LOW     = 2
    NORMAL  = 3
    HIGH    = 4
    INVALID = 5
    GAP     = 6


def main():
    files = ["01_small", "02_boundaries", "03_gap_20min", "04_invalid_values", "05_long_record", "06_empty", "07_single_point", "08_missing_rpm", "09_wrong_type", "10_duplicate_time"]
    for filei in range(len(files)):
        files[filei] = SPEC_FOLDER + files[filei] + ".json"

    for filename in files:
        result = form_results(filename)
        print(result)


# TODO: Naming sucks?
def form_results(filename: str) -> str:
    result = dict()

    json = open(filename).read()
    dataset = parse_json(json)

    dataset_name = dataset.dataset_id + ".json"
    result[dataset_name] = dict()
    samples = dataset.samples
    check = check_format(samples)
    if check["status"] != "ok":
        result[dataset_name] = { **check }
        return dict_to_json(result)
    result[dataset_name]["status"] = "ok"
    result[dataset_name]["sample_count"] = len(samples)
    stats = analyze_samples(samples)
    result[dataset_name] = { **result[dataset_name], **stats }
    return dict_to_json(result)


def check_format(samples: list) -> dict:
    result = dict()
    # First element of the tuple says if the attribute allows None value
    required_attrs = {
        "t_s":          (False, int, float),
        "pressure_mpa": (True, int, float),
        "rpm":          (True, int, float),
        "valid":        (False, bool,)
    }
    for samplei, sample in enumerate(samples):
        if not all([hasattr(sample, attr) for attr in required_attrs.keys()]):
            result["status"] = "format_error"
            result["category"] = "missing_field"
            # TODO: Point out the specific attribute (not bother for now)
            result["message"] = f"В samples[{samplei}] отсутствует необходимое поле."
            return result
        for field, types in required_attrs.items():
            attr = getattr(sample, field)
            if not any([isinstance(attr, types[1:])]) and not (types[0] == True and attr is None):
                result["status"] = "format_error"
                result["category"] = "wrong_type"
                # TODO: Point out the specific attribute and type (not bother for now)
                result["message"] = f"В samples[{samplei}] поле имеет недопустимый тип."
                return result
        if samplei != len(samples) - 1:
            nextt = samples[samplei + 1]
            if nextt.t_s - sample.t_s <= 0:
                result["status"] = "format_error"
                result["category"] = "non_increasing_time"
                result["message"] = f"samples[{samplei+1}].t_s не превышает предыдущую метку времени."
                return result
    result["status"] = "ok"
    return result


# TODO: Naming sucks?
def analyze_samples(samples: list) -> dict:
    state_stats = collect_state_stats(samples)
    base_stats = form_base_stats(state_stats)
    derived_stats = form_derived_stats(state_stats)
    results = form_stat_results(base_stats, derived_stats)
    return results


def form_stat_results(base_stats: dict, derived_stats: dict) -> dict:
    result = dict()

    for stat, value in derived_stats.items():
        result[str(stat)] = value

    for stat, value in base_stats.items():
        if stat in (BaseStat.LOW, BaseStat.NORMAL, BaseStat.HIGH):
            continue
        result[str(stat)] = value

    result["modes_s"] = {
        "low":    base_stats[BaseStat.LOW],
        "normal": base_stats[BaseStat.NORMAL],
        "high":   base_stats[BaseStat.HIGH]
    }

    return result


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


# NOTE: This function finds intervals in each of the states
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


def form_base_stats(state_stats):
    result = dict()
    for stati, stat in enumerate(BaseStat):
        result[stat] = list(state_stats.values())[stati]
    return result


def form_derived_stats(base_stats):
    result = dict()
    stats = {
        DerivedStat.UNKNOWN: (State.GAP, State.INVALID),
        DerivedStat.WORKING: (State.LOW, State.NORMAL, State.HIGH),
        DerivedStat.SPAN:    (State.STOPPED,) # + UNKNOWN + WORKING
    }
    for stat, components in stats.items():
        result[stat] = 0
        for component in components:
            result[stat] += base_stats[component]
    result[DerivedStat.SPAN] += result[DerivedStat.UNKNOWN] + result[DerivedStat.WORKING]
    return result


# Dict keys must be strings
def dict_to_json(d):
    buffer = list()
    result = _dict_to_json_impl(d, buffer)
    return result


def _dict_to_json_impl(d, buffer, depth=1):
    buffer.append('{\n')
    items = d.items()
    for i, (k, v) in enumerate(items):
        for _ in range(depth):
            buffer.append(' ' * 4)
        buffer.append(f'"{k}": ')
        if isinstance(v, dict):
            _dict_to_json_impl(v, buffer, depth+1)
        else:
            if isinstance(v, str):
                buffer.append(f'"{v}"')
            else:
                buffer.append(f'{v}')
            # Avoid trailing comma
            if i != len(items) - 1:
                buffer.append(',')
            buffer.append('\n')
    for _ in range(depth-1):
        buffer.append(' ' * 4)
    buffer.append('}\n')
    result = ''.join(buffer)
    return result


if __name__ == "__main__":
    main()

