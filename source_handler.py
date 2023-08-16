import csv
from typing import MutableMapping
from main import Row, Header
from config_handler import Config


class Source:
    name: str
    debug: bool
    data: list[Row]
    col_names_map: dict[Header, Header]
    match_by: list[Header]
    rules: MutableMapping[Header, str]  # sections from configparser objects are not dicts but act like them

    def __init__(self, config: Config, source_name: str, debug: bool = False):
        self.name = source_name
        self.debug = debug

        header_row_num = config.getint(source_name, "header_row_num")
        ignored_rows = parse_ignored_rows(config[source_name]["ignored_rows"])
        self.data = self.__parse_csv(header_row_num, ignored_rows)

        self.col_names_map = config.cols_name_mapping[source_name]
        self.match_by = config[source_name]["match_by"].split(",")
        
        rules_section = f"{source_name}_rules"
        if rules_section in config:
            self.rules = config[f"{source_name}_rules"]
        else:
            self.rules = {}

    def __parse_csv(self, header_row_num: int, ignored_rows: list[int]) -> list[Row]:
        """
        Parses a csv file into a list of its rows. Each row is put into a dictionary where the keys are the headers for a
        column and the values are the elements of that row. Rows listed in ignored_rows are not parsed. The header row is
        not an element of the list, but is represented in every element of the list by the key values.

        :param header_row_num: line number of the headers (starts at 0)
        :param ignored_rows: List of row numbers to ignore
        :return: List of the rows of the csv
        """
        try:
            with open(self.name, newline='', errors="ignore") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.readline())
                csvfile.seek(0)

                header_reader = csv.reader(csvfile, dialect=dialect)
                for _ in range(header_row_num):
                    header_reader.__next__()

                headers: list[str] = header_reader.__next__()
                csvfile.seek(0)

                reader = csv.DictReader(csvfile, fieldnames=headers, dialect=dialect)

                rows: list[Row] = []
                for i, row in enumerate(reader):
                    if self.debug:
                        print(f"Line #{i}: {row}")
                    if i in ignored_rows or i == header_row_num:
                        continue

                    rows.append(row)
        except FileNotFoundError:
            raise SystemExit(f"Could not find {self.name}")

        return rows


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
