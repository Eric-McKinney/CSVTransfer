"""
Project Description

This script will transfer data from one csv to another into a new file. Any number of columns to transfer may be given.
Only one column from each csv can be used to match by, however. This "matching" is necessary because the transfer might
not just be a copy-paste of a column, rather the data might be in a different order or might not have the same number of
rows.


Usage

First, before running this script make sure that the two csv files you want to operate on are in the same directory as
this script. Once you've done that, you can run this script. A config file may be provided or input can be taken from
stdin when prompted. An example config file can be seen in config_example.txt.
"""
import configparser
import csv
import os
import sys

# Custom types for clarity
Header = str
Data = str
Row = dict[Header: Data]

# TODO: Switch to standard configparser library
# TODO: Add command line argument for config file
# TODO: Update documentation
# TODO: Make a README

HELP_MSG = """
Usage

py main.py [SOURCE_FILE] [TARGET_FILE]
\t\tEnsure that both files are in the same directory as this script or a subdirectory (use relative path).
\t\tSee README for more extensive detail.
"""


def main(args: list[str] = None):
    if args is None:
        if len(sys.argv) > 1:
            args = sys.argv[1:]
        else:
            args = [input("Source file: "), input("Target file: ")]

    if ["-h", "--help"] in args:
        print(HELP_MSG)
        exit(0)

    if not valid_args(args):
        raise SystemExit("See README for proper usage or use --help")

    config: dict = get_config_constants()
    print("="*80)
    print("Parsing source...", end="", flush=True)
    parsed_source: list[Row] = parse_csv(args[0], config["source"]["header_row_num"],
                                         config["source"]["ignored_rows"])
    print("DONE\nParsing target...", end="", flush=True)
    parsed_target: list[Row] = parse_csv(args[1], config["target"]["header_row_num"],
                                         config["target"]["ignored_rows"])
    print("DONE")

    print("Transferring data...", end="", flush=True)
    transfer_data(parsed_source, parsed_target, config["target_columns"], config["match_by"])
    print("DONE\nWriting results to output file...", end="", flush=True)
    write_csv(config["output_file_name"], parsed_target, config["writing_dialect"])
    print(f"DONE\n\nResults can be found in {config['output_file_name']}")


def valid_args(args: list[str]) -> bool:
    """
    Determines if arguments are valid. Arguments should be two file names or relative paths of files

    :param args: List of command line arguments
    :return: True if valid, false if not valid
    """
    for arg in args:
        # If the args aren't files in the current directory then we can't proceed.
        path: str = os.path.join(os.getcwd(), arg)
        path_exists: bool = os.path.exists(path)
        is_file: bool = os.path.isfile(path)
        if not path_exists or not is_file:
            print(f"Invalid arg: '{arg}'", file=sys.stderr)
            print(f"{path} exists" if path_exists else f"{path} does not exist", file=sys.stderr)
            print("Is a file" if is_file else "Is not a file", file=sys.stderr)
            return False

    if len(args) > 2:
        print("Too many arguments", file=sys.stderr)
    elif len(args) < 2:
        print("Too few arguments", file=sys.stderr)

    return len(args) == 2


def get_config_constants() -> configparser.ConfigParser:
    """
    Assigns config constants from the file .csv_transfer.ini which is described in the README. Does extra parsing on
    variables which need to be put into a data structure.

    :return: Dictionary of the constants where the keys are the name of the constants
    """

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(".csv_transfer.ini")

    # Collect missing variables via stdin
    for section in ["source", "target"]:
        for key in ["target_column", "match_by"]:
            if config[section][key] is None:
                config[section][key] = input(f"{key} missing for {section}. Input manually: ")

    return config


def parse_unprocessed_fields(config: configparser.ConfigParser) -> None:
    pass


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
                if i in ignored_rows or i == header_line_num:
                    continue

                rows.append(row)
    except FileNotFoundError:
        print(f"Could not find {file_name}", file=sys.stderr)
        exit(1)

    return rows


def transfer_data(source: list[Row], target: list[Row], target_columns: dict[str: str],
                  match_by: tuple[str, str]) -> None:
    """
    Moves data from target column(s) (keys of target_columns dictionary) in the parsed source file to the target
    column(s) (values of target_columns dictionary) in the parsed target file. This is done for all the values in the
    source file from the column specified by match_by (the first string). If a value in the source file from the column
    specified by match_by does not have a matching value in the target file in the corresponding match_by column (second
    string) then the data for that value is not transferred.

    :param source: Parsed source file
    :param target: Parsed target file
    :param target_columns: Column(s) whose data will be transferred in source-destination pairs
    :param match_by: Column from each file to align data by in order of source, target
    :return:
    """

    for row in source:
        data_to_match_by: str = row[match_by[0]]
        data_to_transfer: dict[str: str] = {}

        for header in target_columns.keys():
            data_to_transfer[header] = row[header]

        for t_row in target:
            if t_row[match_by[1]] == data_to_match_by:
                for header in target_columns.keys():
                    t_header = target_columns[header]
                    t_row[t_header] = data_to_transfer[header]

                break


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
