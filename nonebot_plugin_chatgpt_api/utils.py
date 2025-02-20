import fnmatch
import json
import os
from typing import List


def find_files(dir, name_pattern):
    """
    Search for files matching a specified pattern in a given directory and its subdirectories.

    Args:
    - dir: String of root directory path to search.
    - name_pattern: String of pattern to match filename against (e.g. '*.txt' to match all txt files).

    Returns:
    - A list of full paths to the found files.
    """
    matches = []
    if not os.path.exists(dir):
        return []
    else:
        for root, dirs, files in os.walk(dir):
            for filename in fnmatch.filter(files, name_pattern):
                matches.append(os.path.join(root, filename))
        return matches


def create_dir(dir, suppress_errors=False):
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
    except Exception as e:
        if suppress_errors:
            print(f"{e}\n(This exception have been suppressed and would not influence the program execution)")
        else:
            raise e


def load_json(file_path):
    with open(file_path, "r", encoding="utf8") as f:
        data = json.load(f)
    return data


def load_jsonl(file_path) -> List:
    data = []
    with open(file_path, "r", encoding="utf8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error decoding line: {line}")
                continue
    return data
