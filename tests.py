import unittest
import main


class MyTestCase(unittest.TestCase):
    def test_parse_csv(self):
        parsed_csv: list[main.Row] = main.parse_csv("example.csv", 0)
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
        parsed_csv: list[main.Row] = main.parse_csv("example2.csv", 0)
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
        parsed_csv: list[main.Row] = main.parse_csv("example3.csv", 1)
        expected_parsed_csv: list[main.Row] = [
            {"social security": "", "d.o.b": "", "last name first name": "Bob Joe", "employment status": "employed",
             "favorite color": "Teal", "hobbies": "Tennis", "comments": ""},
            {"social security": "1234321", "d.o.b": "", "last name first name": "Wayne Emily", "employment status": "",
             "favorite color": "Red", "hobbies": "", "comments": "No comment"},
            {"social security": "234111", "d.o.b": "1/1/1970", "last name first name": "Last First",
             "employment status": "", "favorite color": "Green", "hobbies": "Deliberate misinformation",
             "comments": "Mr. Unix Epoch"},
            {"social security": "", "d.o.b": "", "last name first name": "", "employment status": "", "favorite color": "", "hobbies": "", "comments": ""},
            {"social security": "565", "d.o.b": "", "last name first name": "", "employment status": "employed",
             "favorite color": "Royal purple", "hobbies": "No hobby", "comments": ""}
        ]

        self.assertEqual(expected_parsed_csv, parsed_csv)


if __name__ == '__main__':
    unittest.main()
