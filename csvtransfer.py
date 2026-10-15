import argparse
import configparser as cfg
import os
import pandas as pd
import pprint
import sys


DEBUG = False


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
    parser.add_argument("--strict", action="store_true",
                        help="joins work like unions (i.e. an inner join)")

    args = parser.parse_args(sys.argv[1:])

    global DEBUG
    DEBUG = args.debug

    config = parse_config(args.config_file_path)
    validate_config(config)

    if "defaults" in config:
        set_default_configurations(config)


def debug_print(msg: str, indent: int = 0) -> None:
    if DEBUG:
        print("  " * indent, file=sys.stderr, end="")
        print(msg, file=sys.stderr)


def dump_config(config: cfg.ConfigParser) -> None:
    config_dict = dict(config)
    config_dict.pop("DEFAULT")  # added by configparser

    for section_name, section in config_dict.items():
        config_dict[section_name] = dict(section)

    pprint.pp(config_dict, stream=sys.stderr)


def parse_config(config_file_path: str) -> cfg.ConfigParser:
    debug_print(f"finding configuration file {config_file_path}...")

    if not os.path.exists(os.path.join(os.getcwd(), config_file_path)):
        raise SystemExit(f"error: config file \"{config_file_path}\" does not exist")

    debug_print("parsing configuration file...")

    config = cfg.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config.read(config_file_path)

    debug_print("dumping parsed configuration...")
    if DEBUG:
        dump_config(config)

    return config


def section_exists(config: cfg.ConfigParser, section_name: str) -> str:
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


def key_exists(config: cfg.ConfigParser, section_name: str, key: str, use_default=True) -> str:
    default_exists = ("defaults" in config
                 and key in config["defaults"]
                 and config["defaults"][key] not in [None, ""])

    if section_name in config and (not use_default or not default_exists):
        if key not in config[section_name]:
            return f"error: {key} missing from {section_name} section\n"
        if config[section_name][key] in [None, ""]:
            return f"error: {key} has no value in {section_name} section\n"

    return ""


def validate_output_dialect(config: cfg.ConfigParser) -> str:
    valid_dialects = {"excel", "excel_tab", "unix"}
    output_dialect = None

    if "output" in config and "dialect" in config["output"]:
        output_dialect = config["output"]["dialect"]

    if output_dialect not in [None, ""] and output_dialect not in valid_dialects:
        return f"error: {output_dialect} is not a valid output dialect (excel, excel_tab, unix)\n"

    return ""


def validate_config(config: cfg.ConfigParser) -> None:
    error_msg = ""
    warn_msg = ""

    debug_print("validating configuration (error & warning messages printed after)...")

    debug_print("checking if required sections exist...", indent=1)
    for required_section in ["sources", "output"]:
        error_msg += section_exists(config, required_section)

    debug_print("checking if source files in sources section exist...", indent=1)
    source_section = config["sources"] if "sources" in config else dict()
    for source_file in source_section.values():
        error_msg += source_csv_exists(source_file)

    debug_print("checking if each source has its own config section...", indent=1)
    for source_name in source_section:
        if source_name not in config:
            error_msg += f"error: source {source_name} has no dedicated config section\n"

    debug_print("checking if required values are in each source section...", indent=1)
    for source_name in source_section:
        for required_key in ["target_columns", "header_row_num"]:
            error_msg += key_exists(config, source_name, required_key)

    debug_print("checking if required values are in output section...", indent=1)
    for required_key in ["file_name", "dialect"]:
        error_msg += key_exists(config, "output", required_key, use_default=False)

    debug_print("checking if output dialect is valid...", indent=1)
    error_msg += validate_output_dialect(config)

    debug_print("checking if any field rules are empty...", indent=1)
    field_rules_section = config["field_rules"] if "field_rules" in config else dict()
    for header in field_rules_section:
        rule = config["field_rules"][header]
        if rule in [None, ""]:
            warn_msg += f"warning: field rule for {header} is empty\n"

    if error_msg != "":
        debug_print("configuration has errors, printing error messages and exiting...")
        raise SystemExit(error_msg.rstrip())

    if warn_msg != "":
        print(warn_msg.rstrip(), file=sys.stderr)


def set_default_configurations(config: cfg.ConfigParser) -> None:
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


if __name__ == "__main__":
    main()
