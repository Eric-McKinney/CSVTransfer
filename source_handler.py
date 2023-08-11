from typing import MutableMapping
from main import Row, Header
from config_handler import Config


class Source:
    name: str
    data: list[Row]
    headers: list[Header]
    rules: MutableMapping[str, str]  # sections from configparser objects are not dicts but act like them

    def __init__(self, config: Config, source_name: str):
        pass


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


def parse_source_rules(config: Config) -> dict[str, MutableMapping[str, str]]:
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
        with open(file_name, newline='', errors="ignore") as csvfile:
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
