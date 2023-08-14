import configparser
import sys
import config_gen
from pathlib import Path
from typing import Any, Iterable
from main import Header


class Config:
    config: configparser.ConfigParser
    cols_name_mapping: dict[str, dict[Header, Header]]
    output_headers: list[Header]

    def __init__(self, config_file_name: str) -> None:
        """
        Reads the config file by the given name, checks for errors and bad inputs, and fills in values from defaults for
        each source section. If any errors or bad inputs are found then an appropriate error message will be printed
        before exiting. If there is no file by the given name, one can be generated before exiting.

        :param config_file_name: Name or path of config file
        """

        if not Path(config_file_name).is_file():
            print(f"\"{config_file_name}\" not found. You may need to change CONFIG_FILE_NAME in {sys.argv[0]}")
            gen_cfg: bool = input("Would you like to generate a config file (y/N)? ").lower() in ["y", "yes"]

            if gen_cfg:
                config_gen.main()
                print("\nMake sure CONFIG_FILE_NAME has the name of your new config file before rerunning")

            exit(1)

        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.optionxform = str
        self.config.read(config_file_name)

        self.__validate()
        self.__set_defaults()

        self.cols_name_mapping = self.__map_columns_names()
        self.output_headers = self.__unify_headers()

        self.__validate_rules()

    def __set_defaults(self) -> None:
        """
        Sets all values of keys in sources that appear in defaults to defaults if not set
        (configparser does this but for all sections, and I don't want that)
        """

        for source in self.config["sources"]:
            for key in self.config["defaults"]:
                source_missing_val: bool = key not in self.config[source] or self.config[source][key] in [None, ""]
                default_val_exists: bool = self.config["defaults"][key] not in [None, ""]

                if source_missing_val and default_val_exists:
                    self.config[source][key] = self.config["defaults"][key]

    def __validate(self) -> None:
        """
        Checks the parsed config file for improper inputs, missing information, and other improper usage. While checking
        for these errors, error messages are accumulated and returned after the config file has been fully checked. If
        there were errors detected then the program will print the error messages and exit.
        """
        err_msg = self.__check_missing_sections()
        err_msg += self.__check_missing_variables()

        if err_msg != "":
            raise SystemExit(err_msg.rstrip())

    def __check_missing_sections(self) -> str:
        err_msg = ""

        # Identify missing vital sections
        for section in ["defaults", "sources", "output"]:
            if section not in self.config:
                err_msg += f"{section} not found in config file\n"

        if "sources" not in self.config:
            return err_msg

        if not valid_file_names(self.config["sources"].values()):
            err_msg += "Invalid source file name(s). Ensure the paths are correct in the config file\n"

        # Identify missing source sections
        for source in self.config["sources"]:
            if source not in self.config:
                err_msg += f"Source section \"{source}\" not found\n"

        if len(self.config["sources"]) == 0:
            err_msg += "No source sections found\n"

        return err_msg

    def __check_missing_variables(self) -> str:
        err_msg = self.__check_missing_variables_sources()
        err_msg += self.__check_missing_variables_output()
        err_msg += self.__check_empty_rules("field_rules")

        return err_msg

    def __check_missing_variables_sources(self) -> str:
        err_msg = ""

        if "sources" not in self.config:
            return err_msg

        for source in self.config["sources"]:
            # Identify missing variables in each source section if the section exists
            if source not in self.config:
                continue

            for key in ["target_columns", "header_row_num"]:
                not_in_source = key not in self.config[source]
                not_in_defaults = key not in self.config["defaults"]

                if not_in_source:
                    err_msg += f"Key {key} not found in {source}\n"
                    continue

                no_value_in_source = True if not_in_source else self.config[source][key] in [None, ""]
                no_value_in_defaults = True if not_in_defaults else self.config["defaults"][key] in [None, ""]

                if no_value_in_source and (not_in_defaults or no_value_in_defaults):
                    err_msg += f"No value for {key} in {source} or in defaults\n"

            source_rules = f"{source}_rules"
            self.__check_empty_rules(source_rules)

        return err_msg

    def __check_missing_variables_output(self) -> str:
        err_msg = ""

        if "output" not in self.config:
            return err_msg

        for key in ["file_name", "dialect"]:
            if key not in self.config["output"]:
                err_msg += f"Output {key} missing\n"
            elif self.config["output"][key] in [None, ""]:
                err_msg += f"No value for output {key}\n"

        valid_dialects = ["excel", "excel_tab", "unix"]
        if "dialect" in self.config["output"] and self.config["output"]["dialect"] not in valid_dialects:
            err_msg += f'Invalid output dialect \"{self.config["output"]["dialect"]}\"\n'

        return err_msg

    def __check_empty_rules(self, rule_type: str):
        err_msg = ""

        if rule_type not in self.config:
            return err_msg

        for header in self.config[rule_type]:
            rule = self.config[rule_type][header]

            if rule in [None, ""]:
                err_msg += f"Empty rule for {header} in {rule_type}\n"

        return err_msg

    def __map_columns_names(self) -> dict[str, dict[Header, Header]]:
        """
        Parses the comma separated lists of target_columns, match_by, column_names, and match_by_names from the config
        file into a dictionary where headers from both target_columns and match_by are mapped to new names given by
        column_names and match_by_names. This is done for each source. If there are a different number of headers than
        names, then names are used up until they run out or there are no more headers. Once names run out, headers will
        be mapped to themselves as new names. The headers from match by are put before the headers from target columns.

        :return: Dictionary with keys for each source containing a dictionary of headers and their corresponding name
                 for the output file
        """
        cols_names_mapping: dict[str, dict[Header, Header]] = {}

        for source in self.config["sources"]:
            target_cols: list[str] = self.config[source]["target_columns"].split(",")
            col_names: list[str] = self.config[source]["column_names"].split(",")

            match_by: list[str] = self.config[source]["match_by"].split(",")
            match_by_names: list[str] = self.config[source]["match_by_names"].split(",")

            # Remove empty strings (happens when config file field is left fully or partially empty)
            for header_list in [target_cols, col_names, match_by, match_by_names]:
                for _ in range(header_list.count("")):
                    header_list.remove("")

            cols_names_mapping[source] = {}
            for i, col in enumerate(match_by):
                if i < len(match_by_names):
                    cols_names_mapping[source][col] = match_by_names[i]
                else:
                    cols_names_mapping[source][col] = col

            for i, col in enumerate(target_cols):
                if i < len(col_names):
                    cols_names_mapping[source][col] = col_names[i]
                else:
                    cols_names_mapping[source][col] = col

        return cols_names_mapping

    def __validate_rules(self):
        """
        Validates the field and source rules from the config file. All field and source rules should apply to a header
        that appears in the output otherwise an appropriate error message will be generated. The program will exit after
        accumulating all applicable error messages and printing them out.
        """
        err_msg = ""

        if "field_rules" in self.config:
            for rule in self.config["field_rules"]:
                if rule not in self.output_headers:
                    err_msg += f"field_rule error: Could not find the header \"{rule}\" in output headers\n"

        for source in self.config["sources"]:
            rules_section = f"{source}_rules"

            if rules_section in self.config:
                for rule in self.config[rules_section]:
                    if rule not in self.output_headers:
                        err_msg += f"{rules_section} error: Could not find the header \"{rule}\" in output headers\n"
        
        if err_msg != "":
            raise SystemExit(err_msg.rstrip())

    def __unify_headers(self) -> list[str]:
        """
        Consolidates the headers from across sources into one list without duplicates.

        :return: A list of headers to be used in the output
        """
        unified_headers: list[str] = ["Sources found in", "Source rules broken"]

        for source in self.cols_name_mapping:
            for header in self.cols_name_mapping[source].values():
                if header not in unified_headers:
                    unified_headers.append(header)

        return unified_headers

    def __getitem__(self, item: Any) -> configparser.SectionProxy:
        return self.config[item]


def valid_file_names(file_names: Iterable[str]) -> bool:
    """
    Determines if file names in config file are valid. File names should be paths (absolute or relative) of files that
    exist. (e.g. file_name, ./file_name, ./subdir/file_name, subdir/file_name).

    :param file_names: List of file names from config file
    :return: True if all are valid, false if any are not valid
    """

    for file in file_names:
        path: Path = Path(file)
        path_exists: bool = path.exists()
        is_file: bool = path.is_file()
        if not path_exists or not is_file:
            print(f"\nInvalid file name: '{file}'", file=sys.stderr)
            print("" if path_exists else f"{path.absolute()} does not exist\n", file=sys.stderr, end="")
            print("" if is_file else f"{file} is not a file", file=sys.stderr)
            return False

    return True
