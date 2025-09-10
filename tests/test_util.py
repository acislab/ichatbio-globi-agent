from src.util import csv_to_json


def test_csv_to_list():
    csv = "name,number\nbarb,1\nbob,2\nbev,3\n"
    as_list = csv_to_json(csv)
    assert as_list == [
        {"name": "barb", "number": "1"},
        {"name": "bob", "number": "2"},
        {"name": "bev", "number": "3"}
    ]