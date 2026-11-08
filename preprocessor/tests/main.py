import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from json_parser import parse_json
from preprocessor import form_total_results

DATASET_FOLDER = "./datasets/"


# TODO: Compare each result with the corresponding entry in "expected_results.json"
def main():
    files = ["01_small", "02_boundaries", "03_gap_20min", "04_invalid_values", "05_long_record", "06_empty", "07_single_point", "08_missing_rpm", "09_wrong_type", "10_duplicate_time"]
    for filei in range(len(files)):
        files[filei] = DATASET_FOLDER + files[filei] + ".json"

    filename = files[0]
    result = form_total_results(filename)
    print(result)


if __name__ == "__main__":
    main()

