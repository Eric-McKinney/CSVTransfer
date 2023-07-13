import configparser
import unittest
import main


class MyTestCase(unittest.TestCase):
    def test_valid_file_names(self):
        names1: list[str] = ["example_files/example.csv", "example_files/example2.csv"]
        names2: list[str] = ["example_files/example2.csv", "example_files/example3.csv"]
        names3: list[str] = ["example_files/example.csv", "example_files/example.csv"]

        self.assertTrue(main.valid_file_names(names1))
        self.assertTrue(main.valid_file_names(names2))
        self.assertTrue(main.valid_file_names(names3))

    def test_invalid_file_names(self):
        names1: list[str] = ["does_not_exist.file", "example_files/example.csv"]
        names2: list[str] = ["example_files/example2.csv", "venv"]

        self.assertFalse(main.valid_file_names(names1))
        self.assertFalse(main.valid_file_names(names2))

    def test_parse_csv(self):
        parsed_csv: list[main.Row] = main.parse_csv("example_files/example.csv", 0, [])
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
        parsed_csv: list[main.Row] = main.parse_csv("example_files/example2.csv", 0, [])
        expected_parsed_csv: list[main.Row] = [
            {"name": "First Last", "ssn": "234111", "fav color": "", "state of residence": "Ohio"},
            {"name": "", "ssn": "987654321", "fav color": "Orange", "state of residence": "Texas"},
            {"name": "John Smith", "ssn": "123456", "fav color": "", "state of residence": "Michigan"},
            {"name": "", "ssn": "1234321", "fav color": "", "state of residence": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv3(self):
        parsed_csv: list[main.Row] = main.parse_csv("example_files/example3.csv", 1, [0, 6, 5])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "", "d.o.b": "", "last name, first name": "Bob, Joe", "employment status": "employed",
             "favorite color": "Teal", "hobbies": "Tennis", "comments": ""},
            {"social security": "1234321", "d.o.b": "5/31/2000", "last name, first name": "Wayne, Emily",
             "employment status": "", "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name, first name": "Last, First",
             "employment status": "employed", "favorite color": "Magenta", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv4(self):
        parsed_csv: list[main.Row] = main.parse_csv("example_files/example3.csv", 1, [0, 2, 5])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "1234321", "d.o.b": "5/31/2000", "last name, first name": "Wayne, Emily",
             "employment status": "", "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name, first name": "Last, First",
             "employment status": "employed", "favorite color": "Magenta", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "565", "d.o.b": "", "last name, first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_get_constants_from_file(self):
        main.CONFIG_FILE_NAME = "example_files/config_example.ini"
        config: configparser.ConfigParser = main.get_config_constants()
        expected_constants: dict = {
            "defaults": {
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "sources": {
                "source1": "example_files/example.csv",
                "source3": "example_files/example3.csv",
            },
            "source1": {
                "target_columns": "Favorite Color",
                "column_names": "favorite color",
                "match_by": "Social Security Number",
                "match_by_names": "social security",
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "source1_rules": {
                "social security": "5"
            },
            "source3": {
                "target_columns": "favorite color",
                "column_names": "",
                "match_by": "social security",
                "match_by_names": "",
                "header_row_num": "1",
                "ignored_rows": "0,5"
            },
            "source3_rules": {
                "favorite color": "a"
            },
            "output": {
                "file_name": "test_outputs/output.csv",
                "unmatched_file_name": "",
                "dialect": "excel"
            }
        }

        self.assertConfigEquals(expected_constants, config)

    def test_get_constants_from_nonexistent_file(self):
        main.CONFIG_FILE_NAME = "does_not_exist_for_test_to_work.ini"
        with self.assertRaises(SystemExit):
            main.get_config_constants()

    def test_get_constants_missing_constants(self):
        main.CONFIG_FILE_NAME = "example_files/empty_config.ini"

        with self.assertRaises(SystemExit):
            main.get_config_constants()

    def test_get_constants_missing_constants2(self):
        main.CONFIG_FILE_NAME = "example_files/empty_config2.ini"

        with self.assertRaises(SystemExit):
            main.get_config_constants()

    def test_get_constants_missing_constants3(self):
        main.CONFIG_FILE_NAME = "example_files/empty_config3.ini"

        with self.assertRaises(SystemExit):
            main.get_config_constants()

    def test_write_to_csv(self):
        sample_data: list[main.Row] = [
            {"Name": "John Deer", "Occupation": "Landscaping"},
            {"Name": "Test", "Occupation": "None"},
            {"Name": "Batman", "Occupation": "Hero"}
        ]
        headers: list[str] = ["Name", "Occupation"]

        main.write_csv("test_outputs/test_output.csv", headers, sample_data, dialect="excel")

        with open("test_outputs/test_output.csv") as f:
            lines = f.readlines()

        expected_lines = [
            "Name,Occupation\n",
            "John Deer,Landscaping\n",
            "Test,None\n",
            "Batman,Hero\n"
        ]

        self.assertEqual(expected_lines, lines)

    def test_transfer_data(self):
        source1: list[main.Row] = [
            {"t": "1", "func1": "2", "func2": "4"},
            {"t": "2", "func1": "4", "func2": ""},
            {"t": "3", "func1": "6", "func2": "88"},
            {"t": "4", "func1": "8", "func2": ""},
            {"t": "5", "func1": "10", "func2": "3"},
            {"t": "6", "func1": "13", "func2": ""},
            {"t": "7", "func1": "19", "func2": "2"}
        ]
        source2: list[main.Row] = [
            {"x": "1", "x^2": "1", "x^3": "1"},
            {"x": "2", "x^2": "4", "x^3": "8"},
            {"x": "3", "x^2": "9", "x^3": "27"},
            {"x": "4", "x^2": "16", "x^3": "64"},
            {"x": "5", "x^2": "25", "x^3": "125"}
        ]
        source1_name = "source1"
        source2_name = "source2"
        names_map1: dict[str: str] = {"t": "t", "func1": "func1", "func2": "func2"}
        names_map2: dict[str: str] = {"x": "t", "x^2": "func1", "x^3": "func2"}
        match_by1: list[str] = []
        match_by2: list[str] = ["x"]

        output = []

        main.transfer_data(source1_name, source1, output, names_map1, match_by1)
        main.transfer_data(source2_name, source2, output, names_map2, match_by2)

        expected_output = [
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "t": "1", "func1": "2",
             "func2": "4"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "t": "2", "func1": "4",
             "func2": "8"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "t": "3", "func1": "6",
             "func2": "88"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "t": "4", "func1": "8",
             "func2": "64"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "t": "5", "func1": "10",
             "func2": "3"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "t": "6", "func1": "13",
             "func2": ""},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "t": "7", "func1": "19",
             "func2": "2"}
        ]

        self.assertEqual(expected_output, output)

    def test_transfer_data2(self):
        source1: list[main.Row] = [
            {"Song": "Power Slam", "Rating": "8/10"},
            {"Song": "Mirror of the World", "Rating": "9/10"},
            {"Song": "Freesia", "Rating": "10/10"},
            {"Song": "Nobody", "Rating": "10/10"},
            {"Song": "HEAVY DAY", "Rating": "11/10"}
        ]
        source2: list[main.Row] = [
            {"song": "Alone Infection", "rating": "9/10"},
            {"song": "Requiem", "rating": "10/10"},
            {"song": "HEAVY DAY", "rating": "9/10"},
            {"song": "505", "rating": "10/10"}
        ]
        source1_name = "source1"
        source2_name = "source2"
        names_map1: dict[str: str] = {"Song": "Song", "Rating": "Rating"}
        names_map2: dict[str: str] = {"song": "Song", "rating": "Rating"}
        match_by1: list[str] = []
        match_by2: list[str] = ["song"]

        output = []
        strict_output = []

        unmatched_out_name: str = "test_outputs/unmatched_transfer2.csv"
        unmatched_out_name2: str = "test_outputs/unmatched_transfer2_strict.csv"

        main.transfer_data(source1_name, source1, output, names_map1, match_by1, unmatched_output=unmatched_out_name)
        main.transfer_data(source2_name, source2, output, names_map2, match_by2, unmatched_output=unmatched_out_name)

        main.transfer_data(source1_name, source1, strict_output, names_map1, match_by1,
                           unmatched_output=unmatched_out_name2, strict=True)
        main.transfer_data(source2_name, source2, strict_output, names_map2, match_by2,
                           unmatched_output=unmatched_out_name2, strict=True)

        with open(unmatched_out_name) as f:
            unmatched_lines: list[str] = f.readlines()
        with open(unmatched_out_name2) as f:
            strict_unmatched_lines: list[str] = f.readlines()

        expected_output = [
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Power Slam",
             "Rating": "8/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Mirror of the World",
             "Rating": "9/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Freesia",
             "Rating": "10/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Nobody",
             "Rating": "10/10"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "Song": "HEAVY DAY",
             "Rating": "11/10"},
            {"Sources found in": "source2", "Source rules broken": "Not checked", "Song": "Alone Infection",
             "Rating": "9/10"},
            {"Sources found in": "source2", "Source rules broken": "Not checked", "Song": "Requiem",
             "Rating": "10/10"},
            {"Sources found in": "source2", "Source rules broken": "Not checked", "Song": "505", "Rating": "10/10"}
        ]
        expected_strict_output = [
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Power Slam",
             "Rating": "8/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Mirror of the World",
             "Rating": "9/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Freesia",
             "Rating": "10/10"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Song": "Nobody",
             "Rating": "10/10"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "Song": "HEAVY DAY",
             "Rating": "11/10"}
        ]

        expected_unmatched_lines: list[str] = [
            "source1 had no unmatched data :)\n",
            "source2 had no unmatched data :)\n"
        ]
        expected_strict_unmatched_lines: list[str] = [
            "source1 had no unmatched data :)\n",
            "Sources found in,Reason it didn't match,song,rating\n",
            "source2,Strict on and no match found,Alone Infection,9/10\n",
            "source2,Strict on and no match found,Requiem,10/10\n",
            "source2,Strict on and no match found,505,10/10\n"
        ]

        self.assertEqual(expected_output, output)
        self.assertEqual(expected_unmatched_lines, unmatched_lines)
        self.assertEqual(expected_strict_output, strict_output)
        self.assertEqual(expected_strict_unmatched_lines, strict_unmatched_lines)

    def test_transfer_data3(self):
        source1: list[dict] = [
            {"File Name": "abc.def", "File Format": "def", "File Size": "300kB", "Marked For Deletion": "True"},
            {"File Name": "important_data.csv", "File Format": "csv", "File Size": "20MB",
             "Marked For Deletion": "False"},
            {"File Name": "funny.jpg", "File Format": "jpg", "File Size": "40MB", "Marked For Deletion": "False"},
            {"File Name": "info.txt", "File Format": "txt", "File Size": "10kB", "Marked For Deletion": "False"},
            {"File Name": "music.mp3", "File Format": "mp3", "File Size": "400MB", "Marked For Deletion": "False"}
        ]
        source2: list[dict] = [
            {"Name": "proj.c", "Size": "89B", "Owner": "npp", "Last Changed": "5/30/23", "Delete?": "n"},
            {"Name": "funny.jpg", "Size": "500TB", "Owner": "me", "Last Changed": "1/20/23", "Delete?": ""},
            {"Name": "music.mp3", "Size": "0B", "Owner": "you", "Last Changed": "3/2/03", "Delete?": ""},
            {"Name": "important_data.csv", "Size": "40GB", "Owner": "root", "Last Changed": "2/2/20", "Delete?": ""},
            {"Name": "new_file", "Size": "1B", "Owner": "Simon Cowell", "Last Changed": "6/1/23", "Delete?": ""}
        ]
        source3: list[dict] = [
            {"name": "Joe", "admin privileges": "y", "last logged in": "2 Sep 2019"},
            {"name": "Brock", "admin privileges": "n", "last logged in": "5 Oct 2020"},
            {"name": "Amy", "admin privileges": "n", "last logged in": "24 Feb 2009"},
            {"name": "Diana", "admin privileges": "y", "last logged in": "18 Jun 2023"}
        ]

        source1_name = "source1"
        source2_name = "source2"
        source3_name = "source3"
        names_map1: dict[str: str] = {"File Name": "Name", "File Size": "Size", "Marked For Deletion": "Delete?"}
        names_map2: dict[str: str] = {"Name": "Name", "Owner": "Owner", "Size": "Size", "Delete?": "Delete?"}
        names_map3: dict[str: str] = {"name": "User", "admin privileges": "Admin?"}
        match_by1: list[str] = []
        match_by2: list[str] = ["Name"]
        match_by3: list[str] = []
        unmatched_out_name = "test_outputs/unmatched_transfer3.csv"

        output = []

        main.transfer_data(source1_name, source1, output, names_map1, match_by1, unmatched_output=unmatched_out_name)
        main.transfer_data(source2_name, source2, output, names_map2, match_by2, unmatched_output=unmatched_out_name)
        main.transfer_data(source3_name, source3, output, names_map3, match_by3, unmatched_output=unmatched_out_name)

        with open(unmatched_out_name) as f:
            unmatched_lines: list[str] = f.readlines()

        expected_output: list[dict] = [
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Name": "abc.def",
             "Size": "300kB", "Delete?": "True"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked",
             "Name": "important_data.csv", "Size": "20MB", "Delete?": "False", "Owner": "root"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "Name": "funny.jpg",
             "Size": "40MB", "Delete?": "False", "Owner": "me"},
            {"Sources found in": "source1", "Source rules broken": "Not checked", "Name": "info.txt",
             "Size": "10kB", "Delete?": "False"},
            {"Sources found in": "source1, source2", "Source rules broken": "Not checked", "Name": "music.mp3",
             "Size": "400MB", "Delete?": "False", "Owner": "you"},
            {"Sources found in": "source2", "Source rules broken": "Not checked", "Name": "proj.c", "Size": "89B",
             "Owner": "npp", "Delete?": "n"},
            {"Sources found in": "source2", "Source rules broken": "Not checked", "Name": "new_file", "Size": "1B",
             "Owner": "Simon Cowell", "Delete?": ""},
            {"Sources found in": "source3", "Source rules broken": "Not checked", "User": "Joe", "Admin?": "y"},
            {"Sources found in": "source3", "Source rules broken": "Not checked", "User": "Brock", "Admin?": "n"},
            {"Sources found in": "source3", "Source rules broken": "Not checked", "User": "Amy", "Admin?": "n"},
            {"Sources found in": "source3", "Source rules broken": "Not checked", "User": "Diana", "Admin?": "y"},
        ]
        expected_unmatched_lines: list[str] = [
            "source1 had no unmatched data :)\n",
            "source2 had no unmatched data :)\n",
            "source3 had no unmatched data :)\n"
        ]

        self.assertEqual(expected_output, output)
        self.assertEqual(expected_unmatched_lines, unmatched_lines)

    def test_everything_together(self):
        main.CONFIG_FILE_NAME = "example_files/config_example.ini"
        config = main.get_config_constants()
        main.main()

        with open(f'{config["output"]["file_name"]}') as f:
            lines = f.readlines()

        expected_constants = {
            "defaults": {
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "sources": {
                "source1": "example_files/example.csv",
                "source3": "example_files/example3.csv",
            },
            "source1": {
                "target_columns": "Favorite Color",
                "column_names": "favorite color",
                "match_by": "Social Security Number",
                "match_by_names": "social security",
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "source1_rules": {
                "social security": "5"
            },
            "source3": {
                "target_columns": "favorite color",
                "column_names": "",
                "match_by": "social security",
                "match_by_names": "",
                "header_row_num": "1",
                "ignored_rows": "0,5"
            },
            "source3_rules": {
                "favorite color": "a"
            },
            "output": {
                "file_name": "test_outputs/output.csv",
                "unmatched_file_name": "",
                "dialect": "excel"
            }
        }

        expected_lines = [
            "Sources found in,Source rules broken,social security,favorite color\n",
            "source1,None,123456,Red\n",
            "source1,None,987654321,Orange\n",
            "\"source1, source3\",\"source1:social security, source3:favorite color\",1234321,Yellow\n",
            "\"source1, source3\",\"source1:social security, source3:favorite color\",234111,Green\n",
            "source3,None,,Teal\n",
            "source3,None,565,Royal purple\n"
        ]

        self.assertEqual(expected_lines, lines)
        self.assertConfigEquals(expected_constants, config)

    def test_everything_together2(self):
        main.CONFIG_FILE_NAME = "example_files/config_example2.ini"
        config = main.get_config_constants()
        main.main()

        with open(f'{config["output"]["file_name"]}') as f:
            lines = f.readlines()

        with open(f'{config["output"]["unmatched_file_name"]}') as f:
            unmatched_lines = f.readlines()

        expected_constants = {
            "defaults": {
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "sources": {
                "example3": "example_files/example3.csv",
                "example": "example_files/example.csv"
            },
            "example3": {
                "target_columns": "employment status,favorite color",
                "column_names": "",
                "match_by": "social security",
                "match_by_names": "social security number",
                "header_row_num": "1",
                "ignored_rows": "0,6,5"
            },
            "example3_rules": {
                "favorite color": "[Rr]",
                "employment status": "^[^E]"
            },
            "example": {
                "target_columns": "Employment Status,Favorite Color",
                "column_names": "employment status,favorite color",
                "match_by": "Social Security Number",
                "match_by_names": "social security number",
                "header_row_num": "0",
                "ignored_rows": "-1"
            },
            "example_rules": {},
            "output": {
                "file_name": "test_outputs/output2.csv",
                "unmatched_file_name": "test_outputs/unmatched2.csv",
                "dialect": "unix"
            },
            "field_rules": {
                "employment status": r"^(([eE]|[uU]ne)mployed)$",
                "social security number": r"^\d+$"
            }
        }

        expected_lines = [
            '"Sources found in","Source rules broken","social security number","employment status",'
            '"favorite color"\n',
            '"example3","example3:favorite color","234111","employed","Magenta"\n',
            '"example","None","123456","Employed","Red"\n',
            '"example","None","987654321","Unemployed","Orange"\n'
        ]

        expected_unmatched_lines = [
            '"Sources found in","Reason it didn\'t match","social security","employment status","favorite color"\n',
            '"example3","Data didn\'t match regex/field_rule","","employed","Teal"\n',
            '"example3","Data didn\'t match regex/field_rule","1234321","","Red"\n',
            '"Sources found in","Reason it didn\'t match","Social Security Number","Employment Status",'
            '"Favorite Color"\n',
            '"example","Data didn\'t match regex/field_rule","1234321","Unknown","Yellow"\n',
            '"example","Data didn\'t match regex/field_rule","234111","Unknown","Green"\n'
        ]

        self.assertEqual(expected_lines, lines)
        self.assertEqual(expected_unmatched_lines, unmatched_lines)
        self.assertConfigEquals(expected_constants, config)

    def assertConfigEquals(self, expected_config: dict[str: dict[str: str]], config: configparser.ConfigParser):
        self.assertEqual(len(expected_config.keys()), len(config.sections()))

        for section in expected_config.keys():
            self.assertEqual(len(expected_config[section].keys()), len(config[section].keys()))
            for key in expected_config[section].keys():
                self.assertEqual(expected_config[section][key], config[section][key])


if __name__ == '__main__':
    unittest.main()
