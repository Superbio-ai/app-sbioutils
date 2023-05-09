from typing import List


def get_nested_value(dictionary: dict, path: List[str]):
    if not path:
        return {}
    res = dictionary.get(path[0], {})
    if len(path) > 1:
        for path_key in path[1:]:
            res = res.get(path_key, {})
    return res
