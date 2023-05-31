
"""
Constants

SOURCE_FILE (string): The csv file name which the data will be drawn from
TARGET_FILE (string): The csv file name which the data will be put into
TARGET_COLUMNS (dictionary/map K: string, V: string): The key strings will be the name of the source column and the
associated string value will be the name of the destination column for the data.
MATCH_BY (tuple string, string):
"""

SOURCE_FILE: str = "DNCA"
TARGET_FILE: str = "Lansweeper"
TARGET_COLUMNS: dict[str: str] = {"Asset Tag Number": "Asset Tag"}  # source: destination
MATCH_BY: tuple[str, str] = ("Serial Number", "Serialnumber")  # name in source, name in target


def main():
    pass


if __name__ == "__main__":
    main()
