"""
Project Description

This script will transfer data from one csv to another into a new file. Any number of columns to transfer may be given.
Only one column from each csv can be used to match by, however. This "matching" is necessary because the transfer might
not just be a copy-paste of a column, rather the data might be in a different order or might not have the same number of
rows.
"""
import sys
from time import sleep

# Custom types for clarity
Header = str
Data = str
Row = dict[Header: Data]


def main():
    read_from_file: bool = input("Read constants from a file (y/[n])? ").lower() in ["y", "yes"]
    constants: dict = get_constants(read_from_file)
    print("Parsing source...", end="", flush=True)
    parsed_source: list[Row] = parse_csv(constants["source_file"], constants["source_header_row_num"])
    print("DONE\nParsing target...", end="", flush=True)
    parsed_target: list[Row] = parse_csv(constants["target_file"], constants["target_header_row_num"])
    print("DONE")

    print("Transferring data...", end="", flush=True)
    transfer_data(parsed_source, parsed_target, constants["target_columns"], constants["match_by"])
    print("DONE\nWriting results to output file...", end="", flush=True)
    write_csv(constants["output_file_name"], parsed_target)
    print(f"DONE\n\nResults can be found in {constants['output_file_name']}")


def get_constants(from_file: bool) -> dict:
    """
    Assigns constants either from a file or from stdin. The constants are as follows:

    - source_file (string): The name of csv file which the data will be drawn from.
      The file should be in the same directory as this script.
    - source_header_row_num (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
    - target_file (string): The name of csv file which the data will be put into. The file should be in the same
      directory as this script.
    - target_header_row_num (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
    - output_file_name (string): The name of the resulting csv file (include the file extension).
    - target_columns (dictionary/map K: string, V: string): Indicates the source & destination column pair(s). The
      source column is the key and the destination column is the associated value.
    - match_by (tuple string, string): The column in each csv file to match the data by (e.g. serial number). The data
      in these columns should be shared or mostly the same between the two files. The names of the columns don't need to
      match.

    :param from_file: True if the constants should be loaded from a file, false if constants should be given via stdin
    :return: Dictionary of the constants where the keys are the name of the constants
    """

    constants: dict = {
        "source_file": "",
        "source_header_row_num": 0,
        "target_file": "",
        "target_header_row_num": 0,
        "output_file_name": "",
        "target_columns": {},  # source col: destination col
        "match_by": ("", "")  # col in source, col in target
    }

    if from_file:
        constants_file_name: str = input("Please type the name of the file: ")
        try:
            with open(constants_file_name) as f:
                # Each line is split at the " = " and the latter half is used (without the newline)
                constants["source_file"] = f.readline().split(" = ")[-1].rstrip()
                constants["source_header_row_num"] = int(f.readline().split(" = ")[-1].rstrip())
                constants["target_file"] = f.readline().split(" = ")[-1].rstrip()
                constants["target_header_row_num"] = int(f.readline().split(" = ")[-1].rstrip())
                constants["output_file_name"] = f.readline().split(" = ")[-1].rstrip()
                target_columns_str: str = f.readline().split(" = ")[-1].rstrip()
                match_by_str: str = f.readline().split(" = ")[-1].rstrip()
        except FileNotFoundError:
            print("Could not find file. Make sure the file is in the same directory as this script.", file=sys.stderr)
            exit(1)
    else:
        constants["source_file"] = input("What is the name of the source file? ")
        constants["source_header_row_num"] = int(input("What row contains the headers (first row is 0)? "))
        constants["target_file"] = input("What is the name of the target file? ")
        constants["target_header_row_num"] = int(input("What row contains the headers (first row is 0)? "))
        constants["output_file_name"] = input("Give a name for the output file: ")
        target_columns_str: str = input("Give a comma separated list of the columns of data to be moved in pairs of "
                                        "sources and destinations (in that order).\nEx: source1,dest1,source2,dest2"
                                        "\nEnter here: ")
        match_by_str: str = input("Give the names of the columns which the data being transferred should be matched by "
                                  "in the order of source then target.\nEx: serialnum,serial number\nEnter here: ")

    # Converting from a comma separated list to a dictionary
    target_columns = {}
    prev: str = ""
    for i, col in enumerate(target_columns_str.split(",")):
        if i % 2 == 1:
            target_columns[prev] = col
        else:
            prev = col

    constants["target_columns"] = target_columns
    constants["match_by"] = tuple(match_by_str.split(","))  # Converting from a comma separated pair to a tuple

    return constants


def parse_csv(file_name: str, header_line_num: int) -> list[Row]:
    """
    Parses a csv file into a list of its rows. Each row is put into a dictionary where the keys are the headers for a
    column and the values are the elements of that row. Rows before the header row are ignored. The header row is not an
    element of the list, but is represented in every element of the list by the key values.

    :param file_name: name of file to parse
    :param header_line_num: line number of the headers (starts at 0)
    :return: List of the rows of the csv
    """

    try:
        with open(file_name) as csvfile:
            lines = csvfile.readlines()
    except FileNotFoundError:
        print(f"Could not find {file_name}", file=sys.stderr)
        exit(1)

    # removing newlines and checking for quotes
    lines_with_quotes: list[int] = []
    for i, line in enumerate(lines):
        lines[i] = line.rstrip()

        if i >= header_line_num and "\"" in line:
            lines_with_quotes.append(i)

    headers: list[str] = []
    rows: list[Row] = []
    for i, line in enumerate(lines):
        if i < header_line_num:
            continue

        if i in lines_with_quotes:
            line = normalize_line_with_quotes(line)

        if i == header_line_num:
            headers = line.split(",")
        else:
            rows.append({k: v for (k, v) in zip(headers, line.split(","))})

    return rows


def normalize_line_with_quotes(line: str) -> str:
    """
    Normalizes a line of text by removing the commas and quotes from quoted fields. Does nothing for lines that are
    already normalized.
    Ex: one,two,"extra, commas",three --> one,two,extra commas,three

    :param line: A string of text representing a line from a csv file
    :return: Normalized line
    """

    if "\"" not in line:
        return line

    separated_by_quoted_item: list[str] = line.split("\"")

    quoted_item = separated_by_quoted_item[1]
    normalized_quoted_item = quoted_item.replace(",", "")

    normalized_line: str = separated_by_quoted_item[0] + normalized_quoted_item + separated_by_quoted_item[2]

    return normalized_line


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

    sleep(2)
    pass


def write_csv(file_name: str, data: list[Row]) -> None:
    """
    Formats and writes data to a csv from a list of rows where each row is a dictionary containing keys which are the
    headers and values which are the elements of that row. If there is no file by the given name, one will be created.

    :param file_name: Name of file to be written to or created
    :param data: Data to write to the file
    :return:
    """

    sleep(2)
    pass


if __name__ == "__main__":
    main()
