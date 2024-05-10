#!/usr/bin/env python
from brontes.domain.utils.cobie import validate_spreadsheet
from brontes.domain.models import Facility
import argparse

parser = argparse.ArgumentParser(description='Validate a COBie spreadsheet')
parser.add_argument('--path', type=str, help='The path to the COBie spreadsheet')
parser.add_argument('--output', type=str, help='The path to the output COBie spreadsheet', default=None)
args = parser.parse_args()

path = args.path
output_path = args.output

example_facility = Facility(
  uri="https://syyclops.com/example/example",
  name="Example Facility"
)

# Validate the COBie spreadsheet
with open(path, 'rb') as file:
  file_content = file.read()

  errors_found, errors, updated_file = validate_spreadsheet(file_content=file_content)
  if errors_found:
    print(errors)
    if output_path:
      with open(output_path, 'wb') as output_file:
        output_file.write(updated_file)
  else:
    print("No errors found in the COBie spreadsheet!")