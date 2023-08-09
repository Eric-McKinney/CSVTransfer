import configparser
import sys
import config_gen
from pathlib import Path
from main import Header


class Config2:  # temp name which will take place of the Config type alias eventually
    config: configparser.ConfigParser
    cols_name_mapping: dict[str, dict[Header, Header]]
    all_headers: list[Header]
    # etc idk...

    def __init__(self, config_file_name: str):
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

    def validate(self):
        pass


