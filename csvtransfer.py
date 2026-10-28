import argparse
import configparser as cfg
import os
import pandas as pd
import pprint
import re
import sys


DEBUG = False
SEP = "=" * 80
MINOR_SEP = "-" * 80


def main():
    parser = argparse.ArgumentParser(
            prog="csvtransfer",
            description="Transfer, filter, and consolidate data from an \
                    arbitrary number of csv files.",
            epilog="See the README for more info \
                    <https://github.com/Eric-McKinney/CSVTransfer/blob/main/README.md>")
    
    parser.add_argument("config_file_path", metavar="CONFIG_FILE",
                        help="the path to the configuration file")
    parser.add_argument("--debug", action="store_true",
                        help="enables diagnostic messages")

    args = parser.parse_args(sys.argv[1:])

    global DEBUG
    DEBUG = args.debug

    config = parse_config(args.config_file_path)
    debug_print(SEP)
    validate_config(config)
    debug_print(SEP)

    if "defaults" in config:
        set_default_configurations(config)
        debug_print(SEP)

    parse_source_config_fields(config)
    output_columns = get_output_columns(config)
    debug_print(SEP)
    validate_output_filters(config, output_columns)
    debug_print(SEP)


    output_df = pd.DataFrame()
    output_df = read_and_transfer_data_to_output(config, output_df, output_columns)
    debug_print(SEP)
    apply_output_filters(config["output_filters"], output_df)
    debug_print(SEP)
    write_output_data(config, output_df)


def debug_print(msg: str, indent: int = 0, end: str = "\n") -> None:
    if DEBUG:
        print("  " * indent, file=sys.stderr, end="")
        print(msg, file=sys.stderr, end=end)


def parse_config(config_file_path: str) -> Dict[str,Dict[str,str]]:
    debug_print(f"finding configuration file {config_file_path}...")

    if not os.path.exists(os.path.join(os.getcwd(), config_file_path)):
        raise SystemExit(f"error: config file \"{config_file_path}\" does not exist")

    debug_print("parsing configuration file...")

    config = cfg.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config.read(config_file_path)

    # ConfigParser object is somewhat restrictive, so convert to dictionary
    config = dict(config)
    config.pop("DEFAULT")  # added by configparser, not going to use so remove it
    for section_name, section in config.items():
        config[section_name] = dict(section)

    debug_print("dumping parsed configuration...")
    if DEBUG:
        pprint.pp(config, stream=sys.stderr)

    return config


def section_exists(config: Dict[str,Dict[str,str]], section_name: str) -> str:
    if section_name not in config:
        return f"error: {section_name} section missing from config file\n"

    return ""


def source_csv_exists(source_file: str) -> str:
    path = os.path.join(os.getcwd(), source_file)

    if not os.path.exists(path):
        return f"error: source file {source_file} doesn't exist\n"

    if not os.path.isfile(path):
        return f"error: source file {source_file} exists, but is not a file\n"

    return ""


def key_exists(config: Dict[str,Dict[str,str]], section_name: str, key: str,
               use_default=True) -> str:
    default_exists = ("defaults" in config
                 and key in config["defaults"]
                 and config["defaults"][key] not in [None, ""])

    if section_name in config and (not use_default or not default_exists):
        if key not in config[section_name]:
            return f"error: {key} missing from {section_name} section\n"
        if config[section_name][key] in [None, ""]:
            return f"error: {key} has no value in {section_name} section\n"

    return ""


def validate_output_dialect(config: Dict[str,Dict[str,str]]) -> str:
    valid_dialects = {"csv", "excel"}
    output_dialect = None

    if "output" in config and "dialect" in config["output"]:
        output_dialect = config["output"]["dialect"]

    if output_dialect not in [None, ""] and output_dialect not in valid_dialects:
        return f"error: {output_dialect} is not a valid output dialect (csv, excel)\n"

    return ""


def validate_config(config: Dict[str,Dict[str,str]]) -> None:
    error_msg = ""
    debug_print("validating configuration (error & warning messages printed after)...")

    debug_print("checking if required sections exist...", indent=1)
    for required_section in ["sources", "output"]:
        error_msg += section_exists(config, required_section)

    debug_print("checking if source files in sources section exist...", indent=1)
    sources_section = config["sources"] if "sources" in config else dict()
    for source_file in sources_section.values():
        error_msg += source_csv_exists(source_file)

    debug_print("checking if each source has its own config section...", indent=1)
    for source_name in sources_section:
        if source_name not in config:
            error_msg += f"error: source {source_name} has no dedicated config section\n"

    debug_print("checking if required values are in each source section...", indent=1)
    for source_name in sources_section:
        for required_key in ["target_columns", "header_row_num"]:
            error_msg += key_exists(config, source_name, required_key)

    debug_print("checking if each source's join_by_columns are present in target_columns...",
                indent=1)
    for source_name in sources_section:
        target_cols = config[source_name].get("target_columns", "").split(",")
        join_cols = config[source_name].get("join_by_columns", "").split(",")

        for col in join_cols:
            if col not in target_cols:
                error_msg += f"error: joining column {col} is not a target column for " \
                             f"source {source_name}\n"

    debug_print("checking if required values are in output section...", indent=1)
    for required_key in ["file_name", "dialect"]:
        error_msg += key_exists(config, "output", required_key, use_default=False)

    debug_print("checking if output dialect is valid...", indent=1)
    error_msg += validate_output_dialect(config)

    if error_msg != "":
        debug_print("configuration has errors, printing error messages and exiting...")
        raise SystemExit(error_msg.rstrip())


def parse_source_config_fields(config: Dict[str,Dict[str,str]]) -> None:
    # extra parsing to get source config fields into more useful data types
    for source_name in config["sources"]:
        source = config[source_name]
        source["target_columns"] = source["target_columns"].split(",")

        if "join_by_columns" not in source:
            source_configs["join_by_columns"] = ""

        source["join_by_columns"] = source["join_by_columns"].split(",")
        source["header_row_num"] = int(source["header_row_num"])
        source["ignore_rows"] = list(map(int, source["ignore_rows"].split(",")))


def remap_column(config: Dict[str,Dict[str,Any]], source_name: str, header: str) -> str:
    remapping_section_name = f"{source_name}_column_remapping"
    if remapping_section_name not in config:
        return header

    remapping_section = config[remapping_section_name]

    if header not in remapping_section:
        return header

    debug_print(f"remapped {header} to {remapping_section[header]}", indent=2)
    return remapping_section[header]


def get_output_columns(config: Dict[str,Dict[str,Any]]) -> List[str]:
    join_cols: Set[str] = set()
    data_cols: Set[str] = set()
    debug_print("getting full list of output columns...")

    for source_name in config["sources"]:
        debug_print(f"getting columns from source {source_name}...", indent=1)
        tcols = config[source_name]["target_columns"]
        remap_col = lambda col: remap_column(config, source_name, col)

        if "join_by_columns" in config[source_name]:
            join_by = config[source_name]["join_by_columns"]
            tcols = list(filter(lambda x: x not in join_by, tcols))
            join_cols |= set(map(remap_col, join_by))

        data_cols |= set(map(remap_col, tcols))

    join_cols = list(join_cols)
    data_cols = list(data_cols)
    join_cols.sort()
    data_cols.sort()

    source_tracking_cols = [f"from {source_name}" for source_name in config["sources"]]
    data_cols.extend(source_tracking_cols)

    # put columns being used to join data at the front
    output_columns = join_cols + data_cols
    debug_print(f"output columns: {output_columns}", indent=1)
    return output_columns


def validate_output_filters(config: Dict[str,Dict[str,Any]],
                            output_columns: List[str]) -> None:
    warn_msg = ""
    filters_section = config.get("output_filters", dict())
    debug_print("validating output filters...")

    debug_print("checking if any output filters are empty...", indent=1)
    for header in filters_section:
        rule = config["output_filters"][header]
        if rule in [None, ""]:
            warn_msg += f"warning: output filter for {header} is empty\n"

    debug_print("checking if any filters apply to columns not in output...", indent=1)
    for header in filters_section:
        if header not in output_columns:
            warn_msg += f"warning: output filter for {header} column when no " \
                        f"{header} column exists in output\n"

    if warn_msg != "":
        print(warn_msg.rstrip(), file=sys.stderr)


def set_default_configurations(config: Dict[str,Dict[str,Any]]) -> None:
    debug_print("setting default values in configuration...")
    for source in config["sources"]:
        for key in config["defaults"]:
            if key not in config[source]:
                config[source][key] = None

            source_key = config[source][key]
            default_key = config["defaults"][key]

            if source_key in [None, ""] and default_key not in [None, ""]:
                debug_print(f"{key} empty/missing in {source} section, applying "
                            f"default value {default_key}", indent=1)
                config[source][key] = default_key


def read_and_transfer_data_to_output(config: Dict[str,Dict[str,Any]],
                                     output_df: pd.DataFrame,
                                     output_columns: List[str]) -> pd.DataFrame:
    debug_print("collecting source data into output data...")
    for source_name in config["sources"]:
        source_df = read_source(config, source_name)

        debug_print("renaming columns according to mappings in config...", indent=1)
        mappings = config[f"{source_name}_column_remapping"]
        source_df.rename(columns=mappings, inplace=True)

        # need to rename join_by_columns to join data now that the columns are renamed
        remap_col = lambda col: remap_column(config, source_name, col)
        join_by_cols = config[source_name]["join_by_columns"]
        config[source_name]["join_by_columns"] = list(map(remap_col, join_by_cols))

        output_df = join_data_to_output(config, source_name, source_df, output_df)
        debug_print(MINOR_SEP)

    debug_print("filling N/A values in source tracking columns...")
    for source_name in config["sources"]:
        col = f"from {source_name}"
        output_df[col] = output_df[col].fillna(False)

    output_df = output_df[output_columns]  # ensures columns are in correct order
    debug_print("dumping output data...")
    debug_print(output_df)

    return output_df


def read_source(config: Dict[str,Dict[str,Any]], source_name: str) -> pd.DataFrame:
    debug_print(f"reading source {source_name}'s data...", indent=1)
    source_section = config[source_name]
    csv_file = config["sources"][source_name]

    source_df = pd.read_csv(csv_file,
                            header=source_section["header_row_num"],
                            usecols=source_section["target_columns"],
                            skiprows=source_section["ignore_rows"])

    debug_print(f"dumping source {source_name}'s data...", indent=1)
    debug_print(source_df)
    return source_df


def join_data_to_output(config: Dict[str,Dict[str,Any]], source_name: str,
                        source_df: pd.DataFrame,
                        output_df: pd.DataFrame) -> pd.DataFrame:
    debug_print(f"joining source {source_name}'s data with output data...", indent=1)

    join_by_cols = config[source_name]["join_by_columns"]
    for col in join_by_cols:
        if col not in output_df:
            output_df[col] = []

    source_tracking_col = f"from {source_name}"
    output_df = output_df.merge(source_df, how="outer", on=join_by_cols,
                                suffixes=(None, f"_{source_name}"),
                                indicator=source_tracking_col)

    from_source_series = output_df[source_tracking_col].astype("string")
    from_source_series.replace({"right_only": True, "left_only": False, "both": True},
                               inplace=True)
    output_df[source_tracking_col] = from_source_series

    debug_print(f"finished merging {source_name}, dumping output data...", indent=1)
    debug_print(output_df)
    return output_df


def passes_filters(filters: Dict[str,str], row: pd.Series) -> bool:
    debug_print(f"checking row {row.name}...", indent=1)
    debug_print(f"dumping row...", indent=2)
    debug_print(row)

    for column, regex in filters.items():
        data = row[column]
        debug_print(f"checking filter {regex} for {column} {data}...",
                    indent=2, end="")

        if pd.isna(data):
            debug_print("did not pass (data missing)")
            debug_print("row did not pass all output filters (marked False)", indent=2)
            debug_print(MINOR_SEP)
            return False

        if re.search(pattern=regex, string=str(data)) is None:
            debug_print("did not pass")
            debug_print("row did not pass all output filters (marked False)", indent=2)
            debug_print(MINOR_SEP)
            return False

        debug_print("passed")

    debug_print("row passed all output filters (marked True)", indent=2)
    debug_print(MINOR_SEP)
    return True


def apply_output_filters(filters: Dict[str,str], output_df: pd.DataFrame) -> None:
    debug_print("checking if each row passes output filters...")
    filter_results = output_df.apply(lambda x: passes_filters(filters, x), axis=1)
    output_df.insert(0, "passed output filters", filter_results)


def add_file_extension_if_missing(file_name: str, extension: str) -> str:
    if not file_name.endswith(extension):
        print(f"warning: adding {extension} file extension to output file",
              file=sys.stderr)
        return file_name + extension

    return file_name


def write_output_data(config: Dict[str,Dict[str,Any]], output_df: pd.DataFrame) -> None:
    dialect = config["output"]["dialect"]
    out_file = config["output"]["file_name"]

    file_extension = ".xlsx" if dialect == "excel" else ".csv"
    out_file = add_file_extension_if_missing(out_file, file_extension)

    match dialect:
        case "csv":
            output_df.to_csv(out_file)
        case "excel":
            output_df.to_excel(out_file)
        case _:
            raise SystemExit(f"error: unrecognized output dialect {dialect}")


if __name__ == "__main__":
    main()
