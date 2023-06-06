import unittest
import main


class MyTestCase(unittest.TestCase):
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

    def test_normalize_line(self):
        line1: str = "one,two,three"
        line2: str = "one,\"two, three\""
        line3: str = "\"one, two\",three"
        line4: str = "one,\"two, three\",four"

        normalized_line1: str = main.normalize_line_with_quotes(line1)
        normalized_line2: str = main.normalize_line_with_quotes(line2)
        normalized_line3: str = main.normalize_line_with_quotes(line3)
        normalized_line4: str = main.normalize_line_with_quotes(line4)

        expected_normalized1: str = "one,two,three"
        expected_normalized2: str = "one,two three"
        expected_normalized3: str = "one two,three"
        expected_normalized4: str = "one,two three,four"

        self.assertEqual(expected_normalized1, normalized_line1)
        self.assertEqual(expected_normalized2, normalized_line2)
        self.assertEqual(expected_normalized3, normalized_line3)
        self.assertEqual(expected_normalized4, normalized_line4)

    def test_parse_csv3(self):
        parsed_csv: list[main.Row] = main.parse_csv("example3.csv", 1, [0])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "", "d.o.b": "", "last name first name": "Bob Joe", "employment status": "employed",
             "favorite color": "Teal", "hobbies": "Tennis", "comments": ""},
            {"social security": "1234321", "d.o.b": "", "last name first name": "Wayne Emily", "employment status": "",
             "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name first name": "Last First",
             "employment status": "", "favorite color": "Green", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "", "d.o.b": "", "last name first name": "", "employment status": "",
             "favorite color": "", "hobbies": "", "comments": ""},
            {"social security": "565", "d.o.b": "", "last name first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_parse_csv4(self):
        parsed_csv: list[main.Row] = main.parse_csv("example3.csv", 1, [0, 2, 5])
        expected_parsed_csv: list[main.Row] = [
            {"social security": "1234321", "d.o.b": "", "last name first name": "Wayne Emily", "employment status": "",
             "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name first name": "Last First",
             "employment status": "", "favorite color": "Green", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "565", "d.o.b": "", "last name first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)

    def test_get_constants_from_file(self):
        print("Give the name of a config file that exists\n")
        constants: dict = main.get_constants(True)

        expected_constants: dict = {
            "source_file": "example.csv",
            "source_header_row_num": 0,
            "source_ignored_rows": [],
            "target_file": "example3.csv",
            "target_header_row_num": 1,
            "target_ignored_rows": [0],
            "output_file_name": "output.csv",
            "target_columns": {"Favorite Color": "favorite color"},
            "match_by": ("Social Security Number", "social security")
        }

        self.assertEqual(expected_constants, constants)

    def test_get_constants_from_nonexistent_file(self):
        print("Give the name of a file that doesn't exist\n")

        with self.assertRaises(SystemExit) as cm:
            main.get_constants(True)

        self.assertEqual(1, cm.exception.code)

    def test_get_constants_from_stdin(self):  # Give same inputs for the function call and the test inputs
        print("FUNCTION INPUTS")
        print("="*80)
        constants: dict = main.get_constants(False)

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
            "source_file": input("Source file name: "),
            "source_header_row_num": int(input("Source header row number: ")),
            "source_ignored_rows": input("Ignored rows: ").split(","),
            "target_file": input("Target file name: "),
            "target_header_row_num": int(input("Target header row number: ")),
            "target_ignored_rows": input("Ignored rows: ").split(","),
            "output_file_name": input("Output file name: "),
            "target_columns": {}
        }

        # I wanted the prompts to go in order, but as a result when numbers aren't given empty strings sneak in
        # The rest is just casting to ints from strings
        blanks = 0
        for i, row in enumerate(expected_constants["source_ignored_rows"]):
            if row == "":
                blanks += 1
                continue
            expected_constants["source_ignored_rows"][i] = int(row)
        for _ in range(blanks):
            expected_constants["source_ignored_rows"].remove("")

        blanks = 0
        for i, row in enumerate(expected_constants["target_ignored_rows"]):
            if row == "":
                blanks += 1
                continue
            expected_constants["target_ignored_rows"][i] = int(row)
        for _ in range(blanks):
            expected_constants["target_ignored_rows"].remove("")

        num_target_col_pairs: int = int(input("How many target columns for each file? "))
        for i in range(num_target_col_pairs):
            source_col = input(f"Source target column {i + 1}: ")
            dest_col = input(f"Destination target column {i + 1}: ")
            expected_constants["target_columns"][source_col] = dest_col

        expected_constants["match_by"] = (input("Source file column to match by: "),
                                          input("Target file column to match by: "))

        self.assertEqual(expected_constants, constants)

    def test_write_to_csv(self):
        sample_data: list[main.Row] = [
            {"Name": "John Deer", "Occupation": "Landscaping"},
            {"Name": "Test", "Occupation": "None"},
            {"Name": "Batman", "Occupation": "Hero"}
        ]
        main.write_csv("test_output.csv", sample_data)

        with open("test_output.csv") as f:
            lines = f.readlines()

        expected_lines = [
            "Name,Occupation\n",
            "John Deer,Landscaping\n",
            "Test,None\n",
            "Batman,Hero"
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
        match_by: tuple[str, str] = ("x", "t")

        main.transfer_data(source, target, target_columns, match_by)

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
        match_by: tuple[str, str] = ("Song", "song")

        main.transfer_data(source, target, target_columns, match_by)

        expected_target = [
            {"song": "Alone Infection", "rating": "9/10"},
            {"song": "Requiem", "rating": "10/10"},
            {"song": "HEAVY DAY", "rating": "11/10"},
            {"song": "505", "rating": "10/10"}
        ]

        self.assertEqual(expected_target, target)


if __name__ == '__main__':
    unittest.main()
