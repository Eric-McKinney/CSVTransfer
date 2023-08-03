import configparser
import os

SPECIAL_CHARS = ["*", "'", '"', "?", "!", "^", "`", "$", "/", "\\", "#", "&", "@", "|"]
MAJOR_SEPARATOR = "=" * 80
MINOR_SEPARATOR = "/" + "-"*78 + "/"


def main():
    config_name = validate_name_input(prompt="Config file name: ")

    if os.path.isfile(config_name):
        print(f"{config_name} already exists.")

        overwrite = input("Overwrite it (y/N)? ").lower()
        if overwrite not in ["y", "yes"]:
            print("Exiting")
            exit(0)

    num_sources = int(validate_number_input(prompt="Number of sources (csv files): "))

    config = configparser.ConfigParser()

    config["defaults"] = {
        "header_row_num": "0",
        "ignored_rows": "-1"
    }

    print(MAJOR_SEPARATOR)
    valid_headers = collect_sources_info(config, num_sources)
    collect_output_info(config)
    print(MAJOR_SEPARATOR)
    collect_field_rules(config, valid_headers)
    print(MAJOR_SEPARATOR)

    with open(config_name, "w") as configfile:
        config.write(configfile)
        print(f"{config_name} written")


def contains_special_chars(s: str) -> bool:
    for char in SPECIAL_CHARS:
        if char in s:
            return True

    return False


def validate_name_input(prompt: str, allow_empty: bool = False) -> str:
    val = input(prompt)
    while (not allow_empty and len(val) == 0) or contains_special_chars(val):
        print(f"\"{val}\" is not a valid name. Avoid special characters.")
        val = input(prompt)

    return val


def validate_number_input(prompt: str, allow_empty: bool = False) -> str:
    val = input(prompt)

    if allow_empty and val == "":
        return val

    while not val.isdigit() or int(val) < 0:
        print(f"\"{val}\" is not a valid number")
        val = input(prompt)

    return val


def collect_sources_info(config, num_sources: int) -> set[str]:
    config["sources"] = {}
    valid_headers = set()

    for i in range(num_sources):
        print(f"Source {i + 1}:\n")

        source_name = validate_name_input(f"Give a name for source {i + 1}: ")
        print(MINOR_SEPARATOR)

        csv_path = input(f"Path (absolute or relative to main.py & this script) to the csv file for {source_name}: ")
        while not os.path.isfile(csv_path):
            print(f"{csv_path} either doesn't exist or is not a file.")
            csv_path = input(f"Path to the csv file for {source_name}: ")
        print(MINOR_SEPARATOR)

        col_names_map = collect_target_cols()
        print(MINOR_SEPARATOR)
        target_cols = ",".join(col_names_map.keys())
        col_names = ",".join(col_names_map.values())
        match_by_names_map = collect_match_by()
        print(MINOR_SEPARATOR)
        match_by = ",".join(match_by_names_map.keys())
        match_by_names = ",".join(match_by_names_map.values())
        header_row = validate_number_input(prompt="Header row number (count starting at 0): ")
        print(MINOR_SEPARATOR)
        ignored_rows = collect_ignored_rows()
        print(MINOR_SEPARATOR)
        print("Source rules are regex filters used to flag data. Write the regex so that proper data will match it.")
        valid_headers = {*valid_headers, *col_names_map.values(), *match_by_names_map.values()}
        rules = collect_rules(valid_headers)

        config["sources"][source_name] = csv_path
        config[source_name] = {
            "target_columns": target_cols,
            "column_names": col_names,
            "match_by": match_by,
            "match_by_names": match_by_names,
            "header_row_num": header_row,
            "ignored_rows": ignored_rows
        }
        config[f"{source_name}_rules"] = rules

        print(MAJOR_SEPARATOR)

    return valid_headers


def collect_ignored_rows() -> str:
    ignored_rows = set()

    print("Row numbers will be collected until an empty input is given.")
    row = validate_number_input(prompt="Row to ignore (also starting at 0): ", allow_empty=True)
    while row != "":
        row = validate_number_input(prompt="Row to ignore (also starting at 0): ", allow_empty=True)
        if row == "":
            break
        ignored_rows.add(row)

    return ",".join(ignored_rows)


def collect_field_rules(config, valid_headers: set[str]) -> None:
    print("Field rules are regex filters that allow you to control what gets included in the output. Write the regex "
          "so proper data matches.")

    rules = collect_rules(valid_headers)

    config["field_rules"] = rules


def collect_rules(valid_headers: set[str]) -> dict:
    rules = {}

    print("Rules will be collected until an empty header is given\n")

    header = validate_header_for_rule(valid_headers)
    if header == "":
        return rules
    rule = input("Regex to apply to header: ")

    while header != "":
        rules[header] = rule

        header = validate_header_for_rule(valid_headers)
        if header == "":
            break
        rule = input("Regex to apply to header: ")

    return rules


def validate_header_for_rule(valid_headers: set[str]) -> str:
    header = input("Header (that will appear in output) to apply rule to: ")
    while header not in valid_headers and header != "":
        print(f"\"{header}\" not found in headers that will appear in the output.")
        header = input("Header (that will appear in output) to apply rule to: ")

    return header


def collect_target_cols():
    col_name_map = collect_headers_and_names(header="Target column", h_name="Column name")

    return col_name_map


def collect_match_by():
    match_by_name_map = collect_headers_and_names(header="Match by", h_name="Match by name")

    return match_by_name_map


def collect_headers_and_names(header: str, h_name: str) -> dict[str: str]:
    print(f"Header names will be collected until an empty name is given for {header.lower()}. If {h_name.lower()} is "
          f"left empty then the {header.lower()} (prev input) will be used.\n")
    header_name_map = {}

    col = input(f"{header} (put header from csv): ")
    if col == "":
        return header_name_map

    name = input(f"{h_name} (header to use in output file): ")
    if name == "":
        name = col

    header_name_map[col] = name

    while col != "":
        col = input(f"{header} (put header from csv): ")
        if col == "":
            break

        name = input(f"{h_name} (header to use in output file): ")
        if name == "":
            name = col

        header_name_map[col] = name

    return header_name_map


def collect_output_info(config) -> None:
    config["output"] = {}

    output_file_name = validate_name_input(prompt="Output file name: ")
    print(MINOR_SEPARATOR)
    unmatched_file_name = validate_name_input(prompt="Name of file to send unmatched data to: ", allow_empty=True)
    print(MINOR_SEPARATOR)
    dialect = input("Output dialect (unix/excel_tab/[excel]): ").lower()
    if len(dialect) == 0:
        dialect = "excel"

    while dialect not in ["unix", "excel_tab", "excel"]:
        dialect = input("Output dialect (unix/excel_tab/[excel]): ").lower()
        if len(dialect) == 0:
            dialect = "excel"

    config["output"]["file_name"] = output_file_name
    config["output"]["unmatched_file_name"] = unmatched_file_name
    config["output"]["dialect"] = dialect


if __name__ == "__main__":
    main()
