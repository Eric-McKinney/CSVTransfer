import configparser
import sys
import config_gen
from pathlib import Path
from main import Header


class Config2:  # temp name which will take place of the Config type alias eventually
    config: configparser.ConfigParser
    cols_name_mapping: dict[str, dict[Header, Header]]
    all_headers: list[Header]
    # etc idk...

    def __init__(self, config_file_name: str):
        if not Path(config_file_name).is_file():
            print(f"\"{config_file_name}\" not found. You may need to change CONFIG_FILE_NAME in {sys.argv[0]}")
            gen_cfg: bool = input("Would you like to generate a config file (y/N)? ").lower() in ["y", "yes"]

            if gen_cfg:
                config_gen.main()
                print("\nMake sure CONFIG_FILE_NAME has the name of your new config file before rerunning")

            exit(1)

        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.optionxform = str
        self.config.read(config_file_name)

    def validate(self):
        pass


def valid_file_names(file_names: Iterable[str]) -> bool:
    """
    Determines if file names in config file are valid. File names should be relative paths of files that are within the
    current working directory or a subdirectory. (e.g. file_name, ./file_name, ./subdir/file_name, subdir/file_name).

    :param file_names: List of file names from config file
    :return: True if all are valid, false if any are not valid
    """

    for file in file_names:
        # If files (or relative paths) aren't in the current directory then they are not valid
        path: str = os.path.join(os.getcwd(), file)
        path_exists: bool = os.path.exists(path)
        is_file: bool = os.path.isfile(path)
        if not path_exists or not is_file:
            print(f"\nInvalid file name: '{file}'", file=sys.stderr)
            print("" if path_exists else f"{path} does not exist\n", file=sys.stderr, end="")
            print("" if is_file else f"{file} is not a file", file=sys.stderr)
            return False

    return True


def validate_config(config: Config) -> None:
    """
    Checks the parsed config file for improper inputs, missing information, and other improper usage. While checking for
    these errors, error messages are accumulated and returned after the config file has been fully checked. If there
    were errors detected then the program will print the error messages and exit.

    :param config: Parsed config file
    :return:
    """
    err_msg = ""
    base_sections_exist = True

    # Identify missing vital sections
    for section in ["defaults", "sources", "output"]:
        if section not in config:
            base_sections_exist = False
            err_msg += f"{section} not found in config file\n"

    if base_sections_exist and not valid_file_names(config["sources"].values()):
        err_msg += "Invalid source file name(s). Ensure the paths are correct in the config file\n"

    # Identify missing source sections
    missing_sources = []
    for source in config["sources"]:
        if source not in config:
            err_msg += f"Source section \"{source}\" not found\n"
            missing_sources.append(source)
        elif base_sections_exist:
            for key in config["defaults"]:
                if key not in config[source]:
                    err_msg += f"Key \"{key}\" from defaults not found in {source}. It can be empty, but it needs to " \
                               f"be there\n"

    if base_sections_exist and len(config["sources"]) == 0:
        err_msg += "No source sections found\n"

    # Identify missing variables
    if base_sections_exist:
        for source in config["sources"]:
            # Identify missing variables in each source section if the section exists
            if source in missing_sources:
                continue

            for key in ["target_columns", "header_row_num"]:
                not_in_source = key not in config[source]
                not_in_defaults = key not in config["defaults"]

                if not_in_source:
                    err_msg += f"Key {key} not found in {source}\n"
                    continue

                no_value_in_source = True if not_in_source else config[source][key] in [None, ""]
                no_value_in_defaults = True if not_in_defaults else config["defaults"][key] in [None, ""]

                if no_value_in_source and (not_in_defaults or no_value_in_defaults):
                    err_msg += f"No value for {key} in {source} or in defaults\n"

            # Check for empty source rules
            source_rules = f"{source}_rules"
            if source_rules in config:
                for header in config[source_rules]:
                    rule = config[source_rules]

                    if rule in [None, ""]:
                        err_msg += f"Empty rule \"{header}\" in {source_rules}\n"

        # Identify missing variables in output section
        for key in ["file_name", "dialect"]:
            if key not in config["output"]:
                err_msg += f"Output {key} missing\n"
            elif config["output"][key] in [None, ""]:
                err_msg += f"No value for output {key}\n"

        if "dialect" in config["output"] and config["output"]["dialect"] not in ["excel", "excel_tab", "unix"]:
            err_msg += f'Invalid output dialect \"{config["output"]["dialect"]}\"\n'

    # Check for empty field rules
    if "field_rules" in config:
        for header in config["field_rules"]:
            rule = config["field_rules"][header]

            if rule in [None, ""]:
                err_msg += f"Empty rule for {header} in field_rules\n"

    if err_msg != "":
        raise SystemExit(err_msg.rstrip())


def validate_rules(config: Config, output_headers: list[Header]) -> None:
    """
    Validates the field and source rules from the config file. All field and source rules should apply to a header that
    appears in the output otherwise an appropriate error message will be generated. The program will exit after
    accumulating all applicable error messages and printing them out.

    :param config: Parsed config file
    :param output_headers: List of headers that will appear in the output
    :return:
    """

    err_msg = ""

    if "field_rules" in config:
        for rule in config["field_rules"]:
            if rule not in output_headers:
                err_msg += f"field_rule error: Could not find the header \"{rule}\" in output headers\n"

    for source in config["sources"]:
        rules_section = f"{source}_rules"

        if rules_section in config:
            for rule in config[rules_section]:
                if rule not in output_headers:
                    err_msg += f"{rules_section} error: Could not find the header \"{rule}\" in output headers\n"

    if err_msg != "":
        raise SystemExit(err_msg.rstrip())


def get_config_constants() -> Config:
    """
    Assigns config constants from the file CONFIG_FILE_NAME. Both the constants and the config file are described in the
    README. Exits and prints error message if there are issues with the config file.

    :raises SystemExit: If necessary fields are missing from config file.
    :return: ConfigParser object which acts as a map of the config file where the keys are the sections in the config
    file and the values are dictionaries of that section's variables where the keys are the variable name and the value
    is the value of that variable (as a string).
    """
    if not os.path.exists(os.path.join(os.getcwd(), CONFIG_FILE_NAME)):
        raise SystemExit(f"Could not find config file \"{CONFIG_FILE_NAME}\" in the current directory.\n"
                         f"Either create a config file by that name or change the CONFIG_FILE_NAME variable in this "
                         f"script.")

    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config.read(CONFIG_FILE_NAME)
    validate_config(config)

    # Set all values of keys in sources appear in defaults to defaults if not set
    # (configparser does this but for all sections, and I don't want that)
    for source in config["sources"]:
        for key in config["defaults"]:
            if config[source][key] in [None, ""] and config["defaults"][key] not in [None, ""]:
                config[source][key] = config["defaults"][key]

    return config


def map_columns_names(config: Config) -> dict[str, dict[Header, Header]]:
    """
    Parses the comma separated lists of target_columns, match_by, column_names, and match_by_names from the config
    file into a dictionary where headers from both target_columns and match_by are mapped to new names given by
    column_names and match_by_names. This is done for each source. If there are a different number of headers than
    names, then names are used up until they run out or there are no more headers. Once names run out, headers will be
    mapped to themselves as new names. The headers from match by are put before the headers from target columns.

    :param config: Parsed config file
    :return: Dictionary with keys for each source containing a dictionary of headers and their corresponding name for
             the output file
    """
    cols_names_mapping: dict[str, dict[Header, Header]] = {}

    for source in config["sources"]:
        target_cols: list[str] = config[source]["target_columns"].split(",")
        col_names: list[str] = config[source]["column_names"].split(",")

        match_by: list[str] = config[source]["match_by"].split(",")
        match_by_names: list[str] = config[source]["match_by_names"].split(",")

        # Remove empty strings (happens when config file field is left fully or partially empty)
        for header_list in [target_cols, col_names, match_by, match_by_names]:
            for _ in range(header_list.count("")):
                header_list.remove("")

        cols_names_mapping[source] = {}
        for i, col in enumerate(match_by):
            if i < len(match_by_names):
                cols_names_mapping[source][col] = match_by_names[i]
            else:
                cols_names_mapping[source][col] = col

        for i, col in enumerate(target_cols):
            if i < len(col_names):
                cols_names_mapping[source][col] = col_names[i]
            else:
                cols_names_mapping[source][col] = col

    return cols_names_mapping


def parse_ignored_rows(ignored_rows_str: str) -> list[int]:
    """
    Converts string of comma separated list of row numbers to a list of integers.

    :param ignored_rows_str: Comma separated list of row numbers
    :return: List of row numbers
    """
    ignored_rows: list[int] = []
    for row_num in ignored_rows_str.split(","):
        ignored_rows.append(int(row_num))

    return ignored_rows


def parse_source_rules(config: Config) -> dict[str, configparser.SectionProxy]:
    """
    Creates a dictionary of source names with rules as values. The rules are dictionaries of headers (from the output)
    and the regex to apply for that header.

    :param config: Parsed config file
    :return: Dictionary of each source name (keys) and their rules (values) which are dictionaries of headers and regexs
    """
    source_rules = {}

    for source in config["sources"]:
        if f"{source}_rules" in config:
            rules = config[f"{source}_rules"]
            source_rules[source] = rules

    return source_rules


def unify_headers(names_map: dict[str, dict[Header, Header]]) -> list[Header]:
    """
    Consolidates the headers from across sources into one list without duplicates.

    :param names_map: Map of the headers from each source and their associated name in the output
    :return: A list of headers to be used in the output
    """
    unified_headers: list[str] = ["Sources found in", "Source rules broken"]

    for source in names_map:
        for header in names_map[source].values():
            if header not in unified_headers:
                unified_headers.append(header)

    return unified_headers
