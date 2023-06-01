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

        self.assertEqual(parsed_csv, expected_parsed_csv)

    def test_parse_csv2(self):
        parsed_csv: list[main.Row] = main.parse_csv("example2.csv", 0)
        expected_parsed_csv: list[main.Row] = [
            {"name": "First Last", "ssn": "234111", "fav color": "", "state of residence": "Ohio"},
            {"name": "", "ssn": "987654321", "fav color": "Orange", "state of residence": "Texas"},
            {"name": "John Smith", "ssn": "123456", "fav color": "", "state of residence": "Michigan"},
            {"name": "", "ssn": "1234321", "fav color": "", "state of residence": ""}
        ]

        self.assertEqual(parsed_csv, expected_parsed_csv)


if __name__ == '__main__':
    unittest.main()
