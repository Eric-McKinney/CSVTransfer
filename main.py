__author__ = "Eric McKinney"

"""
Project Description

This script will transfer data from one csv to another into a new file. Any number of columns to transfer may be given.
Only one column from each csv can be used to match by, however. This "matching" is necessary because the transfer might
not just be a copy-paste of a column, rather the data might be in a different order or might not have the same number of
rows.


Usage

First, before running this script make sure that the two csv files you want to operate on are in the same directory as
this script or in a subdirectory. Then make sure you have a config file even if none of the variables have values. An
example config file can be seen in config_example.ini in the example_files directory in GitHub. Once you have a config, 
file you can run this script by typing "py main.py" or "python3 main.py" in the command prompt or shell (while in the 
same directory). If not provided in the config file, necessary values will be taken via stdin when prompted. Values 
entered this way will not be saved to the config file. The name of the config file that this script uses can be changed 
by changing the variable CONFIG_FILE_NAME below.
"""
import configparser
import csv
import os
import re
import sys
from typing import Iterable

# TODO: Add "rules" which data can be flagged by (e.g. only devices of this type should appear here)
# TODO: Update documentation when done with all of the changes

# Custom type aliases for clarity
Header = str
Data = str
Row = dict[Header: Data]

CONFIG_FILE_NAME: str = "config_template.ini"
DEBUG: bool = False  # either change this here or use --debug from command line
HELP_MSG = """USAGE

python3 main.py [OPTION]
py main.py [OPTION]
\tEnsure that both files are in the same directory as this script or a subdirectory (use relative path).
\tSee README for more extensive detail.

OPTIONS
\t--debug
\t\tEnables debug print statements
\t-h, --help
\t\tPrints help message and terminates
\t--strict
\t\tIf data after the first source does not match in at least one of the match_by fields, then the data is considered
\t\tunmatched as opposed to being appended to the output in its own row
"""


def main(args: list[str] = None):
    # TODO: Obviously gonna need to change a bunch of function calls and whatnot
    if args is None:
        if len(sys.argv) > 1:
            args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(HELP_MSG)
        exit(0)

    if "--debug" in args:
        global DEBUG  # I'd prefer not to do this, but this is the only time trust
        DEBUG = True

    strict: bool = "--strict" in args

    config: configparser.ConfigParser = get_config_constants()

    if not valid_file_names(config["sources"].values()):
        raise SystemExit("Invalid source file name(s). Ensure the paths are correct in the config file.")

    print("="*80)

    merged_data: list[Row] = []
    # NOTE: The order of headers in each row dict doesn't matter,
    #       only the order in which they are passed to the DictWriter (fieldnames param) matters
    for source in config["sources"]:
        print(f"Parsing {source}...", end="", flush=True)
        parsed_source: list[Row] = parse_csv(config["sources"][source], config.getint(source, "header_row_num"),
                                             parse_ignored_rows(config["source"]["ignored_rows"]))
        print("DONE", flush=True)

        cols_name_mapping: dict = map_columns_names(config)

        print(f"Transferring {source}'s data...", end="", flush=True)
        transfer_data(source, parsed_source, merged_data, cols_name_mapping, config[source]["match_by"].split(","),
                      unmatched_output=config["output"]["unmatched_file_name"], dialect=config["output"]["dialect"],
                      regex=config["field_rules"], strict=strict)
        print("DONE", flush=True)

    print("Writing results to output file...", end="", flush=True)
    write_csv(config["output"]["file_name"], merged_data, config["output"]["dialect"])
    print(f"DONE\n\nResults can be found in {config['output']['file_name']}")
    print("="*80)


def valid_file_names(file_names: Iterable[str]) -> bool:
    """
    Determines if file names in config file are valid. File names should be relative paths of files that are within the
    current working directory or a subdirectory. (e.g. file_name, ./file_name, ./subdir/file_name).

    :param file_names: List of file names from config file
    :return: True if valid, false if not valid
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


def get_config_constants() -> configparser.ConfigParser:
    """
    Assigns config constants from the file CONFIG_FILE_NAME. Both the constants and the config file are described in the
    README. Exits and prints error message if necessary fields are missing.

    :raises SystemExit: If necessary fields are missing from config file.
    :return: ConfigParser object which acts as a map of the config file where the keys are the sections in the config
    file and the values are dictionaries of that section's variables where the keys are the variable name and the value
    is the value of that variable (as a string).
    """
    if not os.path.exists(os.path.join(os.getcwd(), CONFIG_FILE_NAME)):
        raise SystemExit(f"Could not find config file '{CONFIG_FILE_NAME}' in the current directory.\n"
                         f"Either create a config file by that name or change the CONFIG_FILE_NAME variable in this "
                         f"script.")

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(CONFIG_FILE_NAME)

    # Set all values of keys in sources appear in defaults to defaults if not set
    # (configparser does this but for all sections, and I don't want that)
    for source in config["sources"]:
        for key in config["defaults"]:
            if config[source][key] in [None, ""] and config["defaults"][key] not in [None, ""]:
                config[source][key] = config["defaults"][key]

    # Identify missing variables
    if len(config["sources"]) == 0:
        raise SystemExit("No sources found in config file")

    missing: str = ""
    for source in config["sources"]:
        for key in ["target_column(s)", "header_row_num"]:
            if config[source][key] in [None, ""]:
                missing += f"{key} missing for {source}\n"
    for key in ["file_name", "dialect"]:
        if config["output"][key] in [None, ""]:
            missing += f"Output {key} missing\n"

    if missing != "":
        raise SystemExit(missing.rstrip())

    return config


def map_columns_names(config: configparser.ConfigParser) -> dict[str: dict[Header: Header]]:
    """
    Parses the comma separated lists of target columns, match by from the config file into a dictionary where headers
    from both target columns and match by are mapped to new names given by column names and match by names. If there are
    a different number of headers than names, then names are used up until they run out or there are no more headers.
    Once names run out, headers will be mapped to themselves as new names. Match by are put before target columns.

    :param config: Parsed config file
    :return: Dictionary with source target column(s) as keys w/corresponding columns from target file as values
    """
    cols_names_mapping: dict[str: dict[Header: Header]] = {}

    for source in config["sources"]:
        target_cols: list[str] = config[source]["target_column(s)"].split(",")
        col_names: list[str] = config[source]["column_name(s)"].split(",")

        match_by: list[str] = config[source]["match_by"].split(",")
        match_by_names: list[str] = config[source]["match_by_name(s)"].split(",")

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
    name that appear in the names_map. A match of the data transferred this way is attempted for data from the source in
    the columns whose headers appear in match_by. The data is matched against data that exists in the output under the
    headers that appear in the names_map as values associated with the keys that are contained in match_by. If a match
    is found then any data that can fill an empty field will be transferred, otherwise nothing will be done and data not
    transferred this way does not count towards the unmatched data. If a match cannot be found then the data to be
    transferred will be appended to the output as long as strict is not true. If strict is true then this data will
    contribute to the unmatched data instead of being included in the output. If regex is given, all data from fields
    present in the dictionary must match the associated regex to be transferred. Data that does not match the regex will
    count towards the unmatched data. If unmatched_output is given a value then unmatched data will be written to that
    file.

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

    unmatched_data: list[dict] = []
    for row in source:
        data_to_transfer: dict[Header: str] = {}  # will contain only the data we want to transfer from the row
        found_match: bool = False

        # Extract data
        data_to_transfer["source(s) found in"] = source_name
        for header in names_map:
            data_to_transfer[header] = row[header]

        if regex is not None and not data_matches_regex(data_to_transfer, names_map, regex):
            unmatched_data.append(data_to_transfer)
            continue

        # attempt to find a match
        for out_row in output:
            for match in match_by:
                if out_row[names_map[match]] == row[match]:
                    found_match = True
                    for header in data_to_transfer:
                        if header == "source(s) found in":  # append source name to output under "source(s) found in"
                            if header not in out_row.keys():
                                out_row[header] = data_to_transfer[header]
                            else:
                                out_row[header] += f", {data_to_transfer[header]}"

                            continue

                        out_header = names_map[header]

                        if out_header not in out_row.keys():  # check if data is already there before moving data
                            out_row[out_header] = data_to_transfer[header]

                    break

        if not strict:
            output.append(data_to_transfer)
        elif unmatched_output not in [None, ""] and not found_match:
            unmatched_data.append(data_to_transfer)

    if unmatched_output not in [None, ""]:
        write_csv(unmatched_output, unmatched_data, dialect)


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

        # since regex matching is done based on headers from output we need to find corresponding source header
        source_header: str = ""
        for s_header in names_map:
            o_header = names_map[s_header]
            if header == o_header:
                source_header = s_header
                break

        if source_header == "":  # if there was no corresponding source header (shouldn't be possible) we have an issue
            print(f"Regex match failed: No source header for output header \"{header}\"", file=sys.stderr)
            return False

        if re.search(pattern=regex[header], string=data[source_header]) is None:
            return False

    return True


def write_csv(file_name: str, data: list[Row], dialect: str) -> None:
    """
    Writes data to a csv from a list of rows where each row is a dictionary containing keys which are the
    headers and values which are the elements of that row using the given dialect. If there is no file by the given
    name, one will be created. If a file by the given name already exists, a prompt will ask if it should be
    overwritten.

    :param file_name: Name of file to be written to or created
    :param data: Data to write to the file
    :param dialect: csv dialect to use for writing
    :return:
    """
    # TODO: Add a headers param so the order can be maintained for stuff like match by cols first
    headers: list[str] = data[0].keys()

    try:
        write_data(file_name, headers, data, dialect)
    except FileExistsError:
        print(f"File \"{file_name}\" already exists", file=sys.stderr)
        overwrite = input("Overwrite it (y/N)? ").lower()

        if overwrite in ["y", "yes"]:
            write_data(file_name, headers, data, dialect, new_file=False)
        else:
            raise SystemExit()


def write_data(file_name: str, headers: list[str], data: list[Row], dialect: str, new_file: bool = True) -> None:
    """
    Writes data to a file by the given name. Will create a file if one by the given name does not exist. If a file by
    the given name exists and the intent is to have it overwritten, new_file should be false.

    :param file_name: Name of file to be written to or created.
    :param headers: List of the headers for csv file.
    :param data: Data to write to the file.
    :param dialect: csv dialect to use for writing
    :param new_file: If true, tries to create a new file and will not overwrite files by the name file_name. If false,
    the behavior is the same, but it will overwrite files by the name file_name without warning.
    :raises FileExistsError: If new_file is true and there is already a file by the name file_name.
    :return:
    """
    with open(file_name, "x" if new_file else "w", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, dialect=dialect)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    main()
