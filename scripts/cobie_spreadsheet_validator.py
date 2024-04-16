#!/usr/bin/env python
from openoperator.domain.model import COBieSpreadsheet
import argparse

parser = argparse.ArgumentParser(description='Validate a COBie spreadsheet')
parser.add_argument('--path', type=str, help='The path to the COBie spreadsheet')
args = parser.parse_args()

path = args.path

# Validate the COBie spreadsheet
with open(path, 'rb') as file:
  spreadsheet = COBieSpreadsheet(file.read())
  errors_found, errors, updated_file = spreadsheet.validate()
  if errors_found:
    print(errors)
  else:
    print("No errors found in the COBie spreadsheet!")