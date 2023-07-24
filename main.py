__author__ = "Eric McKinney"

"""
Project Description

This script transfers select data from an arbitrary number of csv files into a new file. Data can be used to "match by"
effectively merging data which shares at least one "match by" field with other data. Regex filters can be applied to csv
fields/columns. The data that does not match these filters and other data considered unmatched can be output to a file.


Usage

All of this script's behavior hinges on a config file. The format for said config file can be found in the README 
(https://github.com/Eric-McKinney/CSVTransfer/blob/main/README.md). By default the config file name that this script
looks for is config_template.ini, but this can be changed by changing the CONFIG_FILE_NAME variable below. Once you have
a config file, ensure that the csv files you want to use are within the directory you use this script in and that the 
file paths given in the config file are valid. To run this script enter "python3 main.py" or "py main.py" depending on 
your environment.
"""
import configparser
import csv
import os
import re
import sys
from typing import Iterable

# Custom type aliases for clarity
Header = str
Data = str
Row = dict[Header: Data]

CONFIG_FILE_NAME: str = "config_template.ini"
DEBUG: bool = False  # either change this here or use --debug from command line
HELP_MSG = """USAGE

python3 main.py [OPTION]
py main.py [OPTION]
\tEnsure that both files are in the same directory as this script or a subdirectory (use relative path in 
\tconfig file).

\tSee README for more extensive detail. (https://github.com/Eric-McKinney/CSVTransfer/blob/main/README.md)

OPTIONS
\t--debug
\t\tEnables debug print statements
\t-h, --help
\t\tPrints this help message and terminates
\t--strict
\t\tIf data after the first source does not match in at least one of the 
\t\tmatch_by fields, then the data is considered unmatched as opposed to 
\t\tbeing appended to the output in its own row

POTENTIAL ISSUES
\tFile encoding
\t\tCheck if the file is encoded with something like UTF-8-BOM. You can probably just 
\t\topen in Notepad++ and save in UTF-8 which will fix this. You may have to experiment with 
\t\tother methods if not.
"""


def main(args: list[str] = None):
    """
    Runs this script by first parsing args which can be given as a list of strings or via command line, loads info from
    config file, checks validity of file paths, parses and transfers data from each csv one by one, enforces source
    rules on the output data, and finally writes the output to a file.

    :param args: Arguments given by a list of strings (can be provided via command line instead)
    :return:
    """
    if args is None:
        if len(sys.argv) > 1:
            args = sys.argv[1:]
        else:
            args = []

    if "--help" in args or "-h" in args:
        print(HELP_MSG)
        exit(0)

    if "--debug" in args:
        global DEBUG  # I'd prefer not to do this, but this is the only time trust
        DEBUG = True

    strict: bool = "--strict" in args

    config: configparser.ConfigParser = get_config_constants()

    print("="*80)

    merged_data: list[Row] = []
    cols_name_mapping: dict = map_columns_names(config)
    # NOTE: The order of headers in each row dict doesn't matter,
    #       only the order in which they are passed to the DictWriter (fieldnames param) matters
    for source in config["sources"]:
        print(f"Parsing {source}...", end="", flush=True)
        parsed_source: list[Row] = parse_csv(config["sources"][source], config.getint(source, "header_row_num"),
                                             parse_ignored_rows(config[source]["ignored_rows"]))
        print("DONE", flush=True)

        print(f"Transferring {source}'s data...", end="", flush=True)
        field_rules = None if "field_rules" not in config else config["field_rules"]
        transfer_data(source, parsed_source, merged_data, cols_name_mapping[source],
                      config[source]["match_by"].split(","), unmatched_output=config["output"]["unmatched_file_name"],
                      dialect=config["output"]["dialect"], regex=field_rules, strict=strict)
        print("DONE", flush=True)

    print("Enforcing source rule(s)...", end="", flush=True)
    source_rules = parse_source_rules(config)
    enforce_source_rules(merged_data, source_rules)
    print("DONE", flush=True)

    print("Writing results to output file...", end="", flush=True)
    headers: list[str] = unify_headers(cols_name_mapping)
    write_csv(config["output"]["file_name"], headers, merged_data, config["output"]["dialect"])
    print(f"DONE\n\nResults can be found in {config['output']['file_name']}")
    print("="*80)


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


def validate_config(config: configparser.ConfigParser) -> str:
    """
    Checks the parsed config file for improper inputs, missing information, and other improper usage. While checking for
    these errors, error messages are accumulated and returned after the config file has been fully checked. If there
    were no errors detected then the string returned will be empty.

    :param config: Parsed config file
    :return: String with messages for all errors detected or an empty string
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
            err_msg += f"Source section \"{source}\" not found. Values are made lowercase and sections names are case" \
                       f" sensitive. Write your source section names in lower case if that's the issue\n"
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

    return err_msg.rstrip()


def get_config_constants() -> configparser.ConfigParser:
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
    config.read(CONFIG_FILE_NAME)
    errors = validate_config(config)

    if errors != "":
        raise SystemExit(errors)

    # Set all values of keys in sources appear in defaults to defaults if not set
    # (configparser does this but for all sections, and I don't want that)
    for source in config["sources"]:
        for key in config["defaults"]:
            if config[source][key] in [None, ""] and config["defaults"][key] not in [None, ""]:
                config[source][key] = config["defaults"][key]

    return config


def map_columns_names(config: configparser.ConfigParser) -> dict[str: dict[Header: Header]]:
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
    cols_names_mapping: dict[str: dict[Header: Header]] = {}

    for source in config["sources"]:
        target_cols: list[str] = config[source]["target_columns"].split(",")
        col_names: list[str] = config[source]["column_names"].split(",")

        match_by: list[str] = config[source]["match_by"].split(",")
        match_by_names: list[str] = config[source]["match_by_names"].split(",")

        # remove all empty strings from the names (happens when values are not given in config file)
        for names in [col_names, match_by_names]:
            to_remove = []
            for i, name in enumerate(names):
                if name == "":
                    to_remove.insert(0, i)

            for idx in to_remove:
                names.__delitem__(idx)

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


def parse_csv(file_name: str, header_line_num: int, ignored_rows: list[int]):
    """
    Parses a csv file into a list of its rows. Each row is put into a dictionary where the keys are the headers for a
    column and the values are the elements of that row. Rows listed in ignored_rows are not parsed. The header row is
    not an element of the list, but is represented in every element of the list by the key values.

    :param file_name: name of file to parse
    :param header_line_num: line number of the headers (starts at 0)
    :param ignored_rows: List of row numbers to ignore
    :return: List of the rows of the csv
    """
    try:
        with open(file_name, newline='') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.readline())
            csvfile.seek(0)

            header_reader = csv.reader(csvfile, dialect=dialect)
            for _ in range(header_line_num):
                header_reader.__next__()

            headers: list[str] = header_reader.__next__()
            csvfile.seek(0)

            reader = csv.DictReader(csvfile, fieldnames=headers, dialect=dialect)

            rows: list[Row] = []
            for i, row in enumerate(reader):
                if DEBUG:
                    print(f"Line #{i}: {row}")
                if i in ignored_rows or i == header_line_num:
                    continue

                rows.append(row)
    except FileNotFoundError:
        raise SystemExit(f"Could not find {file_name}")

    return rows


def transfer_data(source_name: str, source: list[Row], output: list[Row], names_map: dict[Header: Header],
                  match_by: list[Header], unmatched_output: str = None, dialect: str = "excel",
                  regex: dict[Header: str] = None, strict: bool = False) -> None:
    """
    Moves data from columns in the source whose headers appear in names_map to the output under the corresponding header
    name that appear in the names_map. A match of the data transferred this way is attempted. The data is matched
    against data that exists in the output under the headers that appear in the names_map as values associated with the
    keys that are contained in match_by. If a match is found then any data that can fill an empty field will be
    transferred, otherwise nothing will be done and data not transferred this way does not count towards the unmatched
    data. If a match cannot be found then the data to be transferred will be appended to the output as long as strict is
    not true. If strict is true then this data will contribute to the unmatched data instead of being included in the
    output. If regex is given, all data from fields being transferred must match the associated regex to be transferred.
    Data that does not match the regex will count towards the unmatched data. If unmatched_output is given a value then
    unmatched data will be written to that file.

    :param source_name: Name of the source which the source file represents
    :param source: Parsed source file
    :param output: Destination of data from source files
    :param names_map: Column(s) whose data will be transferred and the names of the columns in the output to put them in
    :param match_by: Columns from source file to align data by
    :param unmatched_output: Name of file to output unmatched values to. If no name is provided, unmatched values will
    not be recorded
    :param dialect: Dialect to write unmatched output in (same dialect as regular output)
    :param regex: Dictionary of fields/headers (keys) and the regex (values) to validate them by
    :param strict: If true, sources after the first must match at least one field from match by to have data transferred
    :return:
    """

    first_source: bool = output == []
    output_copy = output.copy()  # needed for when we search for matches while potentially appending after each loop
    unmatched_data: list[dict] = []
    for row in source:
        data_to_transfer: dict[Header: str] = {}  # will contain only the data we want to transfer from the row
        found_match: bool = False

        # Extract data
        data_to_transfer["Sources found in"] = source_name
        data_to_transfer["Source rules broken"] = "Not checked"
        for header in names_map:
            data_to_transfer[names_map[header]] = row[header]

        if regex is not None and not data_matches_regex(data_to_transfer, names_map, regex):
            data = {"Sources found in": source_name, "Reason it didn't match": "Data didn't match regex/field_rule"}
            for header in names_map:
                data[header] = row[header]

            unmatched_data.append(data)
            continue

        # TODO: Generally optimize match finding
        # TODO: Make find_match its own function
        # TODO: Buffer data being appended to output instead of making a copy of the output
        # attempt to find a match
        for out_row in output_copy:
            for match in match_by:
                out_match = names_map[match]
                if out_match in out_row and out_row[out_match] == row[match]:
                    found_match = True
                    for header in data_to_transfer:
                        if header == "Sources found in":  # append source name to output under "sources found in"
                            if header not in out_row.keys():
                                out_row[header] = data_to_transfer[header]
                            elif source_name not in out_row[header].split(", "):  # avoid duplicates of source names
                                out_row[header] += f", {data_to_transfer[header]}"

                            continue

                        # check if data is already there before moving data
                        if header not in out_row.keys() or out_row[header] in ["", None]:
                            out_row[header] = data_to_transfer[header]

                    break

        if (not strict or first_source) and not found_match:
            output.append(data_to_transfer)
        elif unmatched_output not in [None, ""] and not found_match:
            data = {"Sources found in": source_name, "Reason it didn't match": "Strict on and no match found"}
            for header in names_map:
                data[header] = row[header]

            unmatched_data.append(data)

    if unmatched_output not in [None, ""]:
        append = not first_source

        if unmatched_data == []:
            with open(unmatched_output, "a" if append else "w") as f:
                f.write(f"{source_name} had no unmatched data :)\n")
        else:
            headers: list[str] = ["Sources found in", "Reason it didn't match"]
            headers.extend(names_map.keys())
            write_csv(unmatched_output, headers, unmatched_data, dialect, append=append)


def data_matches_regex(data: dict[Header: str], names_map: dict[Header: Header], regex: dict[Header: str]) -> bool:
    """
    Checks if given row's data that is being transferred matches the given regex for specific fields/headers. If a regex
    appears that refers to data not being transferred, it will be ignored.

    :param data: Dictionary of headers (keys) and associated data (values)
    :param names_map: Mapping of headers in source to headers in output
    :param regex: Dictionary of headers (keys) and associated regex (values) for data to match
    :return: True if all data matches given regex, false otherwise
    """
    for header in regex:
        if header not in names_map.values():  # if regex applies to a field not being transferred do nothing
            continue

        if re.search(pattern=regex[header], string=data[header]) is None:
            return False

    return True


def parse_source_rules(config: configparser.ConfigParser) -> dict[str: dict[Header: str]]:
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


def enforce_source_rules(data: list[Row], rules: dict[str: dict[Header: str]]) -> None:
    """
    Goes through the data checking if source rules are obeyed. All broken rules are documented in the "Source rules
    broken" column with the format "source_name:rule_broken" (quotes not included). If no source rules are broken then
    "None" is put instead (quotes still not included). Source rules are only enforced on rows with data from the
    sources that the rules apply to.

    :param data: List of rows (dict w/header data pairs) representing csv file
    :param rules: Dictionary with the source names (keys) and the rules for each source (values)
    :return:
    """
    for row in data:
        rules_broken: str = ""
        for source_name in rules:
            # if row doesn't contain data from source_name
            if re.search(pattern=source_name, string=row["Sources found in"]) is None:
                continue

            for header in rules[source_name]:
                regex = rules[source_name][header]

                if re.search(pattern=regex, string=row[header]) is None:
                    rules_broken += f"{source_name}:{header}" if rules_broken == "" else f", {source_name}:{header}"

        if rules_broken == "":
            row["Source rules broken"] = "None"
        else:
            row["Source rules broken"] = rules_broken


def unify_headers(names_map: dict[str: dict[Header: Header]]) -> list[str]:
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


def write_csv(file_name: str, headers: list[str], data: list[Row], dialect: str, append: bool = False) -> None:
    """
    Writes data to a csv from a list of rows where each row is a dictionary containing keys which are the
    headers and values which are the elements of that row using the given dialect. If there is no file by the given
    name, one will be created. If a file by the given name already exists, a prompt will ask if it should be overwritten
    unless append is true, in which case the data is appended to said file.

    :param file_name: Name of file to be written to or created
    :param headers: Headers for the output file in the order that they should appear
    :param data: Data to write to the file
    :param dialect: csv dialect to use for writing
    :param append: If true, will append instead of creating a new file/overwriting file after asking
    :return:
    """

    mode = "a" if append else "x"
    try:
        write_data(file_name, mode, headers, data, dialect)
    except FileExistsError:
        print(f"File \"{file_name}\" already exists", file=sys.stderr)
        overwrite = input("Overwrite it (y/N)? ").lower()

        if overwrite in ["y", "yes"]:
            write_data(file_name, "w", headers, data, dialect)
        else:
            raise SystemExit()


def write_data(file_name: str, mode, headers: list[str], data: list[Row], dialect: str) -> None:
    """
    Writes data to a file by the given name using the given mode and dialect.

    :param file_name: Name of file to be written to or created.
    :param mode: What mode to open the file in (w, r, a, etc.)
    :param headers: List of the headers for csv file.
    :param data: Data to write to the file.
    :param dialect: csv dialect to use for writing
    :raises FileExistsError: If mode is "x" and there is already a file by the name file_name.
    :return:
    """
    with open(file_name, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, dialect=dialect)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    main()
