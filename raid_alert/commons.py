import json


def json_object_hook(obj):
    '''
    Hook for json loads to convert ints and floats properly.
    '''
    converted_values = {}
    for k, v in obj.items():
        if isinstance(v, str):
            try:
                converted_values[k] = int(v)
            except ValueError:
                try:
                    converted_values[k] = float(v)
                except ValueError:
                    converted_values[k] = v
        else:
            converted_values[k] = v
    return converted_values


def load_json_to_dict(input_file_path):
    '''
    Load a json file directly to a dictionary
    '''
    with open(input_file_path) as input_file:
        return json.load(input_file, object_hook=json_object_hook)
