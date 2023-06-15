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

# Long term
# TODO: Multiple files cross-referencing (possibly on different fields)
# TODO: in a config file can specify what machine types to expect from what sources (ninite, etc.)

# Custom type aliases for clarity
Header = str
Data = str
Row = dict[Header: Data]

CONFIG_FILE_NAME: str = "config_template.ini"
DEBUG: bool = False  # either change this here or use --debug from command line
HELP_MSG = """USAGE

py main.py [OPTION]
python3 main.py [OPTION]
\tEnsure that both files are in the same directory as this script or a subdirectory (use relative path).
\tSee README for more extensive detail.

OPTIONS
\t--debug
\t\tEnables debug print statements
\t-h, --help
\t\tPrints help message and terminates
"""


def main(args: list[str] = None):
    if args is None:
        if len(sys.argv) > 1:
            args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(HELP_MSG)
        exit(0)

    if "--debug" in args:
        global DEBUG  # I'd prefer not to do this, but this is the only time trust
        DEBUG = True

    config: configparser.ConfigParser = get_config_constants()

    if not valid_file_names([config["source"]["file_name"], config["target"]["file_name"]]):
        raise SystemExit("See README for proper usage or use --help")

    print("="*80)
    print("Parsing source...", end="", flush=True)
    parsed_source: list[Row] = parse_csv(config["source"]["file_name"], config.getint("source", "header_row_num"),
                                         parse_ignored_rows(config["source"]["ignored_rows"]))
    print("DONE\nParsing target...", end="", flush=True)
    parsed_target: list[Row] = parse_csv(config["target"]["file_name"], config.getint("target", "header_row_num"),
                                         parse_ignored_rows(config["target"]["ignored_rows"]))
    print("DONE")

    print("Transferring data...", end="", flush=True)
    transfer_data(parsed_source, parsed_target, parse_target_columns(config), config["source"]["match_by"],
                  config["target"]["match_by"], unmatched_output=config["output"]["unmatched_file_name"],
                  dialect=config["output"]["dialect"])
    print("DONE\nWriting results to output file...", end="", flush=True)
    write_csv(config["output"]["file_name"], parsed_target, config["output"]["dialect"])
    print(f"DONE\n\nResults can be found in {config['output']['file_name']}")


def valid_file_names(file_names: list[str]) -> bool:
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
    README. Does extra parsing on variables which need to be put into a data structure.

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

    # Set header_row_num and ignored_rows to defaults if not set (configparser does this but for all sections, and
    # I don't want that)
    for section in ["source", "target"]:
        for key in ["header_row_num", "ignored_rows"]:
            if config[section][key] in [None, ""] and config["defaults"][key] not in [None, ""]:
                config[section][key] = config["defaults"][key]

    # Collect missing variables via stdin
    for section in ["source", "target"]:
        for key in config[section]:
            if config[section][key] in [None, ""]:
                config[section][key] = input(f"{key} missing for {section}. Input manually: ")
    for key in ["file_name", "dialect"]:
        if config["output"][key] in [None, ""]:
            config["output"][key] = input(f"Output {key} missing. Input manually: ")

    return config


def parse_target_columns(config: configparser.ConfigParser) -> dict[str: str]:
    """
    Parses the comma separated lists of target columns from the config file into a dictionary.

    :param config: Parsed config file
    :return: Dictionary with source target column(s) as keys w/corresponding columns from target file as values
    """
    source_target_cols: list[str] = config["source"]["target_column(s)"].split(",")
    target_target_cols: list[str] = config["target"]["target_column(s)"].split(",")

    if len(source_target_cols) != len(target_target_cols):
        raise SystemExit("Number of target column(s) must be the same for source and target\n"
                         f"{len(source_target_cols)} target columns for source found\n"
                         f"{len(target_target_cols)} target columns for target found")

    return {k: v for (k, v) in zip(source_target_cols, target_target_cols)}


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
        print(f"Could not find {file_name}", file=sys.stderr)
        exit(1)

    return rows


def transfer_data(source: list[Row], target: list[Row], target_columns: dict[str: str], source_match_by: str,
                  target_match_by: str, unmatched_output: str = None, dialect: str = "excel",
                  regex: dict[Header: str] = None) -> None:
    """
    Moves data from target column(s) (keys of target_columns dictionary) in the parsed source file to the target
    column(s) (values of target_columns dictionary) in the parsed target file. This is done for all the values in the
    source file from the column specified by source_match_by. If a value in the source file from the column specified
    by source_match_by does not have a matching value in the target file in the corresponding target_match_by column
    then the data for that value is not transferred. If unmatched_output is given a value, unmatched data will be
    written to that file. If regex is given, all data from fields present in the dictionary must match the associated
    regex to be transferred. Data that does not match the regex will count towards the unmatched data.

    :param source: Parsed source file
    :param target: Parsed target file
    :param target_columns: Column(s) whose data will be transferred in source-destination pairs
    :param source_match_by: Column from source file to align data by
    :param target_match_by: Column from target file to align data by
    :param unmatched_output: Name of file to output unmatched values to. If no name is provided, unmatched values will
    not be recorded
    :param dialect: Dialect to write unmatched output in (same dialect as regular output)
    :param regex: Dictionary of fields/headers (keys) and the regex (values) to validate them by
    :return:
    """
    unmatched_data: list[dict] = []
    for row in source:
        data_to_match_by: str = row[source_match_by]
        data_to_transfer: dict[Header: str] = {}
        found_match: bool = False

        # Extract data
        for header in target_columns.keys():
            data_to_transfer[header] = row[header]

        if regex is not None and not data_matches_regex(data_to_transfer, regex):
            data_to_transfer[source_match_by] = data_to_match_by
            unmatched_data.append(data_to_transfer)
            continue

        for t_row in target:
            if t_row[target_match_by] == data_to_match_by:
                found_match = True
                for header in target_columns.keys():
                    t_header = target_columns[header]
                    t_row[t_header] = data_to_transfer[header]

                break

        if unmatched_output not in [None, ""] and not found_match:
            data_to_transfer[source_match_by] = data_to_match_by
            unmatched_data.append(data_to_transfer)

    if unmatched_output not in [None, ""]:
        write_csv(unmatched_output, unmatched_data, dialect)


def data_matches_regex(data: dict[Header: str], regex: dict[Header: str]) -> bool:
    """
    Checks if given row's data that is being transferred matches the given regex for specific fields/headers. If a regex
    appears that refers to data not being transferred, it will be ignored.

    :param data: Dictionary of headers (keys) and associated data (values)
    :param regex: Dictionary of headers (keys) and associated regex (values) for data to match
    :return: True if all data matches given regex, false otherwise
    """
    for field in regex:
        if field not in data.keys():
            continue

        if re.search(pattern=regex[field], string=data[field]) is None:
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
    headers: list[str] = data[0].keys()

    try:
        write_data(file_name, headers, data, dialect)
    except FileExistsError:
        print(f"File \"{file_name}\" already exists", file=sys.stderr)
        overwrite = input("Overwrite it (y/N)? ").lower()

        if overwrite in ["y", "yes"]:
            write_data(file_name, headers, data, dialect, new_file=False)
        else:
            exit(1)


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
