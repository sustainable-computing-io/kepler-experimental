import yaml
import re
import typing as typing


def replace_vars(input: str, var_lookup: dict[str, typing.Any]) -> str:
    """
    Replaces all occurrences of "${variable_name}" in the input_string
    with the corresponding values from the var_dict dictionary.

    Parameters:
    input_string (str): The string containing variable placeholders.
    var_dict (dict): A dictionary mapping variable names to their values.

    Returns:
    str: The modified string with variables replaced.
    """

    # Define a regex pattern to match ${variable_name}
    pattern = r'\${(.*?)}'

    # Function to replace matched variables with their values from the dictionary
    def replace_match(match: re.Match) -> str:
        var_name = match.group(1)
        return f"{var_lookup.get(var_name, match.group(0))}"  # Return the value or the original placeholder

    # Use re.sub to replace all occurrences of the pattern

    result = re.sub(pattern, replace_match, input)
    return result


def process_pipelines(pipelines, vars):
    for pipeline in pipelines:
        for name, promql in pipeline["features"].items():
            pipeline["features"][name] = replace_vars(promql, vars)
    return pipelines


def load_pipeline(file):
    """Load the pipeline configuration from a YAML file."""

    with open(file) as f:
        config = yaml.safe_load(f)

    vars = config["train"]["vars"] or {}
    process_pipelines(config["train"]["pipelines"], vars)
    config["train"]["target"] = replace_vars(config["train"]["target"], vars)
    return config
