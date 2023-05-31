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
Data = str | int
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
    parsed_source: list[Row] = parse_csv(source_file)
    parsed_target: list[Row] = parse_csv(target_file)
    # parse source and target csv files
    # move data in list of dicts
    # write new csv file
    pass


def get_constants(from_file: bool):
    if from_file:
        constants_file_name: str = input("Please type the name of the file: ")
        try:
            with open(constants_file_name) as f:
                f.readline()
        except FileNotFoundError:
            print("Could not find file. Make sure the file is in the same directory as this script.", file=sys.stderr)
            exit(1)
    else:
        pass


def parse_csv(file_name: str) -> list[Row]:
    # read into list of dicts and return
    with open(file_name) as csvfile:
        lines = csvfile.readlines()
        rows: list[dict[str: str]] = []
        for line in lines:
            pass

    return []


if __name__ == "__main__":
    main()
