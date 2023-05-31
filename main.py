"""
Project Description

This script will transfer data from one csv to another in a new file. Any number of columns to transfer may be given.
Only one column can be used to match by, however. This "matching" is necessary because the transfer might not just be a
copy-paste of a column, rather the data might be in a different order or might not have the same number of rows.


Constants

SOURCE_FILE (string): The name of csv file which the data will be drawn from. The file should be in the same directory
as this script.
SOURCE_HEADER_ROW_NUM (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
TARGET_FILE (string): The name of csv file which the data will be put into. The file should be in the same directory as
this script.
TARGET_HEADER_ROW_NUM (int): Row number to use as header (rows before will be ignored). Row numbers start at 0.
OUTPUT_FILE_NAME (string): The name of the resulting csv file (include the file extension).
TARGET_COLUMNS (dictionary/map K: string, V: string): Indicates the source & destination column pair(s). The source 
column is the key and the destination column is the associated value.
MATCH_BY (tuple string, string): The column in each csv file to match the data by (e.g. serial number). The data in
these columns should be shared or mostly the same between the two files. The names of the columns don't need to match.
"""
import sys

SOURCE_FILE: str = "DNCA EIT - Inventory Sheet.csv"
SOURCE_HEADER_ROW_NUM = 0
TARGET_FILE: str = "lansweeper.csv"
TARGET_HEADER_ROW_NUM = 1
OUTPUT_FILE_NAME: str = "output.csv"
TARGET_COLUMNS: dict[str: str] = {"Asset Tag Number": "Asset Tag"}  # source col: destination col
MATCH_BY: tuple[str, str] = ("Serial Number", "Serialnumber")  # col in source, col in target


def main():
    read_from_file: bool = input("Read constants from a file (y/[n])? ").lower() in ["y", "yes"]

    if read_from_file:
        constants_file_name: str = input("Please type the name of the file: ")
        try:
            with open(constants_file_name) as f:
                pass
        except FileNotFoundError:
            print("Could not find file. Make sure the file is in the same directory as this script.", file=sys.stderr)
            exit(1)
    else:
        pass

    # parse source and target csv files
    # move data in list of dicts
    # write new csv file
    pass


def parse_csv(file_name: str) -> list[dict[str: str]]:
    # read into list of dicts and return
    with open(file_name) as csvfile:
        lines = csvfile.readlines()
        rows: list[dict[str: str]] = []
        for line in lines:
            pass

    return []


if __name__ == "__main__":
    main()
