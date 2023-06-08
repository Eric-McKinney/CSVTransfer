import configparser
import unittest
import main


class MyTestCase(unittest.TestCase):
    def test_valid_args(self):
        args1: list[str] = ["example.csv", "example2.csv"]
        args2: list[str] = ["example2.csv", "example3.csv"]
        args3: list[str] = ["example.csv", "example.csv"]

        self.assertTrue(main.valid_args(args1))
        self.assertTrue(main.valid_args(args2))
        self.assertTrue(main.valid_args(args3))

    def test_invalid_args(self):
        args1: list[str] = ["does_not_exist.file", "example.csv"]
        args2: list[str] = ["example2.csv", "venv"]

        self.assertFalse(main.valid_args(args1))
        self.assertFalse(main.valid_args(args2))

    def test_parse_csv(self):
        parsed_csv: list[main.Row] = main.parse_csv("example.csv", 0, [])
        expected_parsed_csv: list[main.Row] = [
            {"Name": "John Smith", "Date of birth": "3/24/1989", "Social Security Number": "123456",
             "Employment Status": "Employed", "Favorite Color": "Red"},
            {"Name": "Joe Bob", "Date of birth": "1/23/4567", "Social Security Number": "987654321",
             "Employment Status": "Unemployed", "Favorite Color": "Orange"},
            {"Name": "Emily Wayne", "Date of birth": "5/31/2000", "Social Security Number": "1234321",
             "Employment Status": "Unknown", "Favorite Color": "Yellow"},
            {"Name": "First Last", "Date of birth": "1/1/1970", "Social Security Number": "234111",
             "Employment Status": "Unknown", "Favorite Color": "Green"}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv2(self):
        parsed_csv: list[main.Row] = main.parse_csv("example2.csv", 0, [])
        expected_parsed_csv: list[main.Row] = [
            {"name": "First Last", "ssn": "234111", "fav color": "", "state of residence": "Ohio"},
            {"name": "", "ssn": "987654321", "fav color": "Orange", "state of residence": "Texas"},
            {"name": "John Smith", "ssn": "123456", "fav color": "", "state of residence": "Michigan"},
            {"name": "", "ssn": "1234321", "fav color": "", "state of residence": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv3(self):
        parsed_csv: list[main.Row] = main.parse_csv("example3.csv", 1, [0])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "", "d.o.b": "", "last name, first name": "Bob, Joe", "employment status": "employed",
             "favorite color": "Teal", "hobbies": "Tennis", "comments": ""},
            {"social security": "1234321", "d.o.b": "", "last name, first name": "Wayne, Emily",
             "employment status": "", "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name, first name": "Last, First",
             "employment status": "", "favorite color": "Green", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "", "d.o.b": "", "last name, first name": "", "employment status": "",
             "favorite color": "", "hobbies": "", "comments": ""},
            {"social security": "565", "d.o.b": "", "last name, first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv4(self):
        parsed_csv: list[main.Row] = main.parse_csv("example3.csv", 1, [0, 2, 5])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "1234321", "d.o.b": "", "last name, first name": "Wayne, Emily",
             "employment status": "", "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name, first name": "Last, First",
             "employment status": "", "favorite color": "Green", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "565", "d.o.b": "", "last name, first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_get_constants_from_file(self):
        config: configparser.ConfigParser = main.get_config_constants()
        expected_constants: dict = {
            "DEFAULT": {
                "header_row_num": "0",
                "ignored_rows": "-1",
                "output_file_name": "output.csv",
                "output_dialect": "excel"
            },
            "source": {
                "header_row_num": "0",
                "ignored_rows": "-1",
                "target_column(s)": "Favorite Color",
                "match_by": "Social Security Number"
            },
            "target": {
                "header_row_num": "1",
                "ignored_rows": "0,5",
                "target_column(s)": "favorite color",
                "match_by": "social security"
            }
        }

        for section in expected_constants:
            for key in expected_constants[section]:
                self.assertEqual(expected_constants[section][key], config[section][key])

    def test_get_constants_from_nonexistent_file(self):
        main.CONFIG_FILE_NAME = "does_not_exist_for_test_to_work.ini"
        with self.assertRaises(SystemExit):
            main.get_config_constants()

    def test_get_constants_from_stdin(self):  # Give same inputs for the function call and the test inputs
        main.CONFIG_FILE_NAME = "config_example2.ini"
        print("FUNCTION INPUTS")
        print("="*80)
        config: configparser.ConfigParser = main.get_config_constants()
        print("="*80)

        print("BEGIN TEST INPUTS")
        print("(Give same inputs as you did for the function otherwise the test will fail)")
        print("\nNote:\tFor some reason I have yet to figure out, the prompts sometimes don't print until after you "
              "enter something.\n\t\tIf you provide input and the next prompt doesn't print then just look through the "
              "code for what should have printed.")
        print("\t\tI've noticed that it usually happens when I scroll up to see what I put for the function inputs in "
              "PyCharm IDE.")
        print("="*80)
        expected_constants: dict = {
            "DEFAULT": {
                "header_row_num": "",
                "ignored_rows": "",
                "output_file_name": input("output_file_name: "),
                "output_dialect": input("output_dialect: ")
            },
            "source": {
                "header_row_num": input("source header_row_num: "),
                "ignored_rows": input("source ignored_rows: "),
                "target_column(s)": input("source target_column(s): "),
                "match_by": input("source match_by: ")
            },
            "target": {
                "header_row_num": input("target header_row_num: "),
                "ignored_rows": input("target ignored_rows: "),
                "target_column(s)": input("target target_column(s): "),
                "match_by": input("target match_by: ")
            }
        }

        for section in expected_constants:
            for key in expected_constants[section]:
                self.assertEqual(expected_constants[section][key], config[section][key])

    def test_write_to_csv(self):
        sample_data: list[main.Row] = [
            {"Name": "John Deer", "Occupation": "Landscaping"},
            {"Name": "Test", "Occupation": "None"},
            {"Name": "Batman", "Occupation": "Hero"}
        ]
        main.write_csv("test_output.csv", sample_data, dialect="excel")

        with open("test_output.csv") as f:
            lines = f.readlines()

        expected_lines = [
            "Name,Occupation\n",
            "John Deer,Landscaping\n",
            "Test,None\n",
            "Batman,Hero\n"
        ]

        self.assertEqual(expected_lines, lines)

    def test_transfer_data(self):
        source: list[main.Row] = [
            {"x": "1", "x^2": "1", "x^3": "1"},
            {"x": "2", "x^2": "4", "x^3": "8"},
            {"x": "3", "x^2": "9", "x^3": "27"},
            {"x": "4", "x^2": "16", "x^3": "64"},
            {"x": "5", "x^2": "25", "x^3": "125"}
        ]
        target: list[main.Row] = [
            {"t": "1", "func1": "2", "func2": "4"},
            {"t": "2", "func1": "4", "func2": ""},
            {"t": "3", "func1": "6", "func2": "88"},
            {"t": "4", "func1": "8", "func2": ""},
            {"t": "5", "func1": "10", "func2": "3"},
            {"t": "6", "func1": "13", "func2": ""},
            {"t": "7", "func1": "19", "func2": "2"}
        ]
        target_columns: dict[str: str] = {"x^2": "func2"}
        source_match_by: str = "x"
        target_match_by: str = "t"

        main.transfer_data(source, target, target_columns, source_match_by, target_match_by)

        expected_target = [
            {"t": "1", "func1": "2", "func2": "1"},
            {"t": "2", "func1": "4", "func2": "4"},
            {"t": "3", "func1": "6", "func2": "9"},
            {"t": "4", "func1": "8", "func2": "16"},
            {"t": "5", "func1": "10", "func2": "25"},
            {"t": "6", "func1": "13", "func2": ""},
            {"t": "7", "func1": "19", "func2": "2"}
        ]

        self.assertEqual(expected_target, target)

    def test_transfer_data2(self):
        source: list[main.Row] = [
            {"Song": "Power Slam", "Rating": "8/10"},
            {"Song": "Mirror of the World", "Rating": "9/10"},
            {"Song": "Freesia", "Rating": "10/10"},
            {"Song": "Nobody", "Rating": "10/10"},
            {"Song": "HEAVY DAY", "Rating": "11/10"}
        ]
        target: list[main.Row] = [
            {"song": "Alone Infection", "rating": "9/10"},
            {"song": "Requiem", "rating": "10/10"},
            {"song": "HEAVY DAY", "rating": "9/10"},
            {"song": "505", "rating": "10/10"}
        ]
        target_columns: dict[str: str] = {"Rating": "rating"}
        source_match_by: str = "Song"
        target_match_by: str = "song"

        main.transfer_data(source, target, target_columns, source_match_by, target_match_by)

        expected_target = [
            {"song": "Alone Infection", "rating": "9/10"},
            {"song": "Requiem", "rating": "10/10"},
            {"song": "HEAVY DAY", "rating": "11/10"},
            {"song": "505", "rating": "10/10"}
        ]

        self.assertEqual(expected_target, target)

    def test_everything_together(self):
        main.CONFIG_FILE_NAME = "config_example.ini"
        config: configparser.ConfigParser = main.get_config_constants()
        args = ["example.csv", "example3.csv"]
        parsed_source: list[main.Row] = main.parse_csv(args[0], config.getint("source", "header_row_num"),
                                                       main.parse_ignored_rows(config["source"]["ignored_rows"]))
        parsed_target: list[main.Row] = main.parse_csv(args[1], config.getint("target", "header_row_num"),
                                                       main.parse_ignored_rows(config["target"]["ignored_rows"]))
        main.transfer_data(parsed_source, parsed_target, main.parse_target_columns(config),
                           config["source"]["match_by"], config["target"]["match_by"])
        main.write_csv(config["DEFAULT"]["output_file_name"], parsed_target, config["DEFAULT"]["output_dialect"])

        with open(config["DEFAULT"]["output_file_name"]) as f:
            lines = f.readlines()

        expected_constants = {
            "DEFAULT": {
                "header_row_num": "0",
                "ignored_rows": "-1",
                "output_file_name": "output.csv",
                "output_dialect": "excel"
            },
            "source": {
                "header_row_num": "0",
                "ignored_rows": "-1",
                "target_column(s)": "Favorite Color",
                "match_by": "Social Security Number"
            },
            "target": {
                "header_row_num": "1",
                "ignored_rows": "0,5",
                "target_column(s)": "favorite color",
                "match_by": "social security"
            }
        }

        expected_lines = [
            "social security,d.o.b,\"last name, first name\",employment status,favorite color,hobbies,comments\n",
            ",,\"Bob, Joe\",employed,Teal,Tennis,\n",
            "1234321,,\"Wayne, Emily\",,Yellow,,No comment\n",
            "234111,1/1/1970,\"Last, First\",,Green,Deliberate misinformation,Mr. Unix Epoch\n",
            "565,,,employed,Royal purple,No hobby,\n"
        ]

        self.assertEqual(expected_lines, lines)
        for section in expected_constants:
            for key in expected_constants[section]:
                self.assertEqual(expected_constants[section][key], config[section][key])


if __name__ == '__main__':
    unittest.main()
