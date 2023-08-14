__author__ = "Eric McKinney"

"""
Project Description

This script transfers select data from an arbitrary number of csv files into a new file. Data can be used to "match by"
effectively merging data which shares at least one "match by" field with other data. Regex filters can be applied to csv
fields/columns. The data that does not match these filters and other data considered unmatched can be output to a file.


Usage

All of this script's behavior hinges on a config file. The format for said config file can be found in the README 
(https://github.com/Eric-McKinney/CSVTransfer/blob/main/README.md). By default the config file name that this script
looks for is config_template.ini, but this can be changed by changing the CONFIG_FILE_NAME variable below. Once you have
a config file, ensure that the csv files you want to use are within the directory you use this script in and that the 
file paths given in the config file are valid. To run this script enter "python3 main.py" or "py main.py" depending on 
your environment.
"""
import configparser
import csv
import re
import sys
from config_handler import Config
from source_handler import Source

# Custom type aliases for clarity
Header = str
Data = str
Row = dict[Header, Data]

CONFIG_FILE_NAME: str = "config_template.ini"
HELP_MSG = """USAGE

python3 main.py [OPTION]
py main.py [OPTION]
\tEnsure that both files are in the same directory as this script or a subdirectory (use relative path in 
\tconfig file).

\tSee README for more extensive detail. (https://github.com/Eric-McKinney/CSVTransfer/blob/main/README.md)

OPTIONS
\t--debug
\t\tEnables debug print statements
\t-h, --help
\t\tPrints this help message and terminates
\t--strict
\t\tIf data after the first source does not match in at least one of the 
\t\tmatch_by fields, then the data is considered unmatched as opposed to 
\t\tbeing appended to the output in its own row

POTENTIAL ISSUES
\tFile encoding
\t\tCheck if the file is encoded with something like UTF-8-BOM. You can probably just 
\t\topen in Notepad++ and save in UTF-8 which will fix this. You may have to experiment with 
\t\tother methods if not.
"""


class CSVTransfer:
    debug: bool
    strict: bool
    config: Config
    output_data: list[Row]
    sources: list[Source]

    def __init__(self, config: Config, strict: bool = False, debug: bool = False):
        self.debug = debug
        self.strict = strict
        self.config = config
        self.output_data = []


def main(args: list[str] = None):
    """
    Runs this script by first parsing args which can be given as a list of strings or via command line, loads info from
    config file, checks validity of file paths, parses and transfers data from each csv one by one, enforces source
    rules on the output data, and finally writes the output to a file.

    :param args: Arguments given by a list of strings (can be provided via command line instead)
    :return:
    """
    if args is None:
        if len(sys.argv) > 1:
            args = sys.argv[1:]
        else:
            args = []

    if "--help" in args or "-h" in args:
        print(HELP_MSG)
        exit(0)

    strict: bool = "--strict" in args
    debug: bool = "--debug" in args

    config: Config = Config(CONFIG_FILE_NAME)
    transfer = CSVTransfer(config, strict=strict, debug=debug)

    merged_data: list[Row] = []

    print("="*80)

    # NOTE: The order of headers in each row dict doesn't matter,
    #       only the order in which they are passed to the DictWriter (fieldnames param) matters
    for source in config["sources"]:
        print(f"Parsing {source}...", end="", flush=True)
        parsed_source: list[Row] = parse_csv(config["sources"][source], config.getint(source, "header_row_num"),
                                             parse_ignored_rows(config[source]["ignored_rows"]))
        print("DONE", flush=True)

        print(f"Transferring {source}'s data...", end="", flush=True)
        field_rules = None if "field_rules" not in config else config["field_rules"]
        transfer_data(source, parsed_source, merged_data, cols_name_mapping[source],
                      config[source]["match_by"].split(","), unmatched_output=config["output"]["unmatched_file_name"],
                      dialect=config["output"]["dialect"], regex=field_rules, strict=strict)
        print("DONE", flush=True)

    print("Enforcing source rule(s)...", end="", flush=True)
    source_rules = parse_source_rules(config)
    enforce_source_rules(merged_data, source_rules)
    print("DONE", flush=True)

    print("Writing results to output file...", end="", flush=True)
    write_csv(config["output"]["file_name"], headers, merged_data, config["output"]["dialect"])
    print(f"DONE\n\nResults can be found in {config['output']['file_name']}")

    if config["output"]["unmatched_file_name"] not in [None, ""]:
        print(f"Unmatched data can be found in {config['output']['unmatched_file_name']}")

    print("="*80)


def transfer_data(source_name: str, source: list[Row], output: list[Row], names_map: dict[Header, Header],
                  match_by: list[Header], unmatched_output: str = None, dialect: str = "excel",
                  regex: dict[Header, str] = None, strict: bool = False) -> None:
    """
    Moves data from columns in the source whose headers appear in names_map to the output under the corresponding header
    name that appear in the names_map. A match of the data transferred this way is attempted. The data is matched
    against data that exists in the output under the headers that appear in the names_map as values associated with the
    keys that are contained in match_by. If a match is found then any data from that row that can fill an empty field
    will be transferred. For the rest of the data from that row nothing will be done (it won't be considered unmatched).
    data. If a match cannot be found then the data to be transferred will be appended to the output as long as strict is
    not true. If strict is true then this data will contribute to the unmatched data instead of being included in the
    output. If regex is given, all data from fields being transferred must match the associated regex to be transferred.
    Data that does not match the regex will count towards the unmatched data. If unmatched_output is given a value then
    unmatched data will be written to that file.

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

    first_source: bool = output == []
    buffer: list[Row] = []  # Buffering instead of appending to output directly to avoid matching data from same source
    unmatched_data: list[Row] = []
    for row in source:
        data_to_transfer: Row = {}  # will contain only the data we want to transfer from the row
        found_match: bool = False

        # Extract data
        data_to_transfer["Sources found in"] = source_name
        data_to_transfer["Source rules broken"] = "Not checked"
        for header in names_map:
            data_to_transfer[names_map[header]] = row[header]

        if regex is not None and not data_matches_regex(data_to_transfer, regex):
            data = {"Sources found in": source_name, "Reason it didn't match": "Data didn't match regex/field_rule"}
            for header in names_map:
                data[header] = row[header]

            unmatched_data.append(data)
            continue

        # attempt to find a match and transfer data if it would go into an empty field
        for out_row in output:
            if rows_match(row, out_row, match_by, names_map):
                found_match = True

                for header in data_to_transfer:
                    if header == "Sources found in":  # append source name to output under "sources found in"
                        if header not in out_row.keys():
                            out_row[header] = data_to_transfer[header]
                        elif source_name not in out_row[header].split(", "):  # avoid duplicates of source names
                            out_row[header] += f", {data_to_transfer[header]}"

                        continue

                    # check if data is already there before moving data
                    if header not in out_row.keys() or out_row[header] in ["", None]:
                        out_row[header] = data_to_transfer[header]

        if (not strict or first_source) and not found_match:
            buffer.append(data_to_transfer)
        elif unmatched_output not in [None, ""] and not found_match:
            data = {"Sources found in": source_name, "Reason it didn't match": "Strict on and no match found"}
            for header in names_map:
                data[header] = row[header]

            unmatched_data.append(data)

    output.extend(buffer)

    if unmatched_output not in [None, ""]:
        append = not first_source

        if unmatched_data == []:
            with open(unmatched_output, "a" if append else "w") as f:
                f.write(f"{source_name} had no unmatched data :)\n")
        else:
            headers: list[str] = ["Sources found in", "Reason it didn't match"]
            headers.extend(names_map.keys())
            write_csv(unmatched_output, headers, unmatched_data, dialect, append=append)


def rows_match(row: Row, out_row: Row, match_by: list[Header],
               names_map: dict[Header, Header]) -> bool:
    """
    Determines whether two rows match one another. Two rows are considered matching if the data under one or more
    specified headers is identical. For the row parameter this means the headers in the match_by list. For the out_row
    parameter this means the headers that are mapped (values) to the headers in the match_by (keys) in the names_map.

    :param row: Row from source
    :param out_row: Row in output
    :param match_by: Headers to match data by
    :param names_map: Mapping of headers in sources to headers in the output
    :return: True if the rows match, false if not
    """
    matches = False

    for match in match_by:
        out_match = names_map[match]
        if out_match in out_row and row[match] != "" and out_row[out_match] == row[match]:
            matches = True
            break

    return matches


def data_matches_regex(data: Row, regex: dict[Header, str]) -> bool:
    """
    Checks if given row's data that is being transferred matches the given regex for specific fields/headers. If a regex
    appears that refers to data not being transferred, it will be ignored.

    :param data: Dictionary of headers (keys) and associated data (values)
    :param regex: Dictionary of headers (keys) and associated regex (values) for data to match
    :return: True if all data matches given regex, false otherwise
    """
    for header in regex:
        if re.search(pattern=regex[header], string=data[header]) is None:
            return False

    return True


def enforce_source_rules(data: list[Row], rules: dict[str, configparser.SectionProxy]) -> None:
    """
    Goes through the data checking if source rules are obeyed. All broken rules are documented in the "Source rules
    broken" column with the format "source_name:rule_broken" (quotes not included). If no source rules are broken then
    "None" is put instead (quotes still not included). Source rules are only enforced on rows with data from the
    sources that the rules apply to.

    :param data: List of rows (dict w/header data pairs) representing csv file
    :param rules: Dictionary with the source names (keys) and the rules for each source (values)
    :return:
    """
    for row in data:
        rules_broken: str = ""
        for source_name in rules:
            # if row doesn't contain data from source_name
            if re.search(pattern=source_name, string=row["Sources found in"]) is None:
                continue

            for header in rules[source_name]:
                regex = rules[source_name][header]

                if re.search(pattern=regex, string=row[header]) is None:
                    rules_broken += f"{source_name}:{header}" if rules_broken == "" else f", {source_name}:{header}"

        if rules_broken == "":
            row["Source rules broken"] = "None"
        else:
            row["Source rules broken"] = rules_broken


def write_csv(file_name: str, headers: list[str], data: list[Row], dialect: str, append: bool = False) -> None:
    """
    Writes data to a csv from a list of rows where each row is a dictionary containing keys which are the
    headers and values which are the elements of that row using the given dialect. If there is no file by the given
    name, one will be created. If a file by the given name already exists, a prompt will ask if it should be overwritten
    unless append is true, in which case the data is appended to said file.

    :param file_name: Name of file to be written to or created
    :param headers: Headers for the output file in the order that they should appear
    :param data: Data to write to the file
    :param dialect: csv dialect to use for writing
    :param append: If true, will append instead of creating a new file/overwriting file after asking
    :return:
    """

    mode = "a" if append else "x"
    try:
        write_data(file_name, mode, headers, data, dialect)
    except FileExistsError:
        print(f"File \"{file_name}\" already exists", file=sys.stderr)
        overwrite = input("Overwrite it (y/N)? ").lower()

        if overwrite in ["y", "yes"]:
            write_data(file_name, "w", headers, data, dialect)
        else:
            return


def write_data(file_name: str, mode, headers: list[str], data: list[Row], dialect: str) -> None:
    """
    Writes data to a file by the given name using the given mode and dialect.

    :param file_name: Name of file to be written to or created.
    :param mode: What mode to open the file in (w, r, a, etc.)
    :param headers: List of the headers for csv file.
    :param data: Data to write to the file.
    :param dialect: csv dialect to use for writing
    :raises FileExistsError: If mode is "x" and there is already a file by the name file_name.
    :return:
    """
    with open(file_name, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, dialect=dialect)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    main()
