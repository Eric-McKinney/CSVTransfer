"""
Project Description

This script will transfer data from one csv to another in a new file. Any number of columns to transfer may be given.
Only one column can be used to match by, however. This "matching" is necessary because the transfer might not just be a
copy-paste of a column, rather the data might be in a different order or might not have the same number of rows.


Config variables

- source_file (string): The name of csv file which the data will be drawn from. The file should be in the same directory
as this script.
- source_header_row_num (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
- target_file (string): The name of csv file which the data will be put into. The file should be in the same directory as
this script.
- target_header_row_num (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
- output_file_name (string): The name of the resulting csv file (include the file extension).
- target_columns (dictionary/map K: string, V: string): Indicates the source & destination column pair(s). The source
column is the key and the destination column is the associated value.
- match_by (tuple string, string): The column in each csv file to match the data by (e.g. serial number). The data in
these columns should be shared or mostly the same between the two files. The names of the columns don't need to match.
"""
import sys

# Custom types for clarity
Header = str
Data = str
Row = dict[Header: Data]

source_file: str = ""
source_header_row_num = 0
target_file: str = ""
target_header_row_num = 0
output_file_name: str = ""
target_columns: Row = {}  # source col: destination col
match_by: tuple[str, str] = ("", "")  # col in source, col in target


def main():
    read_from_file: bool = input("Read constants from a file (y/[n])? ").lower() in ["y", "yes"]
    get_constants(read_from_file)
    parsed_source: list[Row] = parse_csv(source_file, source_header_row_num)
    parsed_target: list[Row] = parse_csv(target_file, target_header_row_num)

    # move data in list of dicts
    # write new csv file
    pass


def get_constants(from_file: bool):
    global source_file, source_header_row_num, target_file, target_header_row_num, output_file_name, target_columns
    global match_by

    if from_file:
        constants_file_name: str = input("Please type the name of the file: ")
        try:
            with open(constants_file_name) as f:
                source_file = f.readline().split(" = ")[-1]
                source_header_row_num = int(f.readline().split(" = ")[-1])
                target_file = f.readline().split(" = ")[-1]
                target_header_row_num = int(f.readline().split(" = ")[-1])
                output_file_name = f.readline().split(" = ")[-1]
                target_columns_str: str = f.readline().split(" = ")[-1]
                match_by_str: str = f.readline().split(" = ")[-1]
        except FileNotFoundError:
            print("Could not find file. Make sure the file is in the same directory as this script.", file=sys.stderr)
            exit(1)
    else:
        source_file = input("What is the name of the file the data will be drawn from? ")
        source_header_row_num = int(input("What row contains the headers (first row is 0)? "))
        target_file = input("What is the name of the file which should be copied with the data put in it? ")
        target_header_row_num = int(input("What row contains the headers (first row is 0)? "))
        output_file_name = input("Give a name for the output file (including file extension): ")
        target_columns_str: str = input("Give a comma separated list of the columns of data to be moved in pairs of "
                                        "sources and destinations (in that order).\nEx: source1,dest1,source2,dest2"
                                        "\nEnter here: ")
        match_by_str: str = input("Give the names of the columns which the data being transferred should be matched by "
                                  "in the order of source then target.\nEx: serialnum,serial number\nEnter here: ")

    target_columns = {}
    prev: str = ""
    for i, col in enumerate(target_columns_str.split(",")):
        if i % 2 == 1:
            target_columns[prev] = col
        else:
            prev = col

    match_by = tuple(match_by_str.split(","))


def parse_csv(file_name: str, header_line_num: int) -> list[Row]:
    with open(file_name) as csvfile:
        lines = csvfile.readlines()

        for i, line in enumerate(lines):
            lines[i] = line.rstrip()

        headers: list[str] = []
        rows: list[Row] = []
        for i, line in enumerate(lines):
            if i < header_line_num:
                continue
            elif i == header_line_num:
                headers = line.split(",")
            else:
                row = {k: v for (k, v) in zip(headers, line.split(","))}
                rows.append(row)

    return rows


if __name__ == "__main__":
    main()
