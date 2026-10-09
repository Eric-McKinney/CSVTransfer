import argparse
import configparser as cfg
import os
import pandas as pd
import sys


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

    config = parse_config(args.config_file_path, args.debug)
    validate_config(config, args.debug)
    set_default_configurations(config, args.debug)



def parse_config(config_file_path: str, debug: bool) -> cfg.ConfigParser:
    if debug:
        print(f"finding configuration file {config_file_path}...")

    if not os.path.exists(os.path.join(os.getcwd(), config_file_path)):
        raise SystemExit(f"error: config file \"{config_file_path}\" does not exist")

    if debug:
        print("parsing configuration file...")

    config = cfg.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config.read(config_file_path)

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


def validate_config(config: cfg.ConfigParser, debug: bool) -> None:
    error_msg = ""

    for section in ["defaults", "sources", "output"]:
        error_msg += section_exists(section)

    for source_file in config["sources"].values():
        error_msg += source_csv_exists(source_file)

    for source_name in config["sources"]:
        if source_name not in config:
            error_msg += f"error: source {source_name} has no dedicated config section\n"

    # TODO: check for missing variables
    # TODO: check for empty field rules
    # TODO: add debug diagnostic messages

    if error_msg != "":
        raise SystemExit(error_msg.rstrip())


def set_default_configurations(config: cfg.ConfigParser) -> None:
    for source in config["sources"]:
        for key in config["defaults"]:
            if key not in config[source]:
                config[source][key] = None

            source_key = config[source][key]
            default_key = config["defaults"][key]

            if source_key in [None, ""] and default_key not in [None, ""]:
                config[source][key] = default_key


if __name__ == "__main__":
    main()
