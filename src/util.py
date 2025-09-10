import csv
import io


def csv_to_json(data: str) -> list:
    csv_file = io.StringIO(data)
    reader = csv.DictReader(csv_file)
    return list(reader)
