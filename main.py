from piscout import *
import csv


# Main method to process a full-page sheet
# Submits three times, because there are three matches on one sheet
def main(scout, file):
    f = open(file + '.csv')
    csvf = csv.reader(f)
    for row in csvf:
        scout.set(row)
    scout.submit()

# This line creates a new PiScout and starts the program
# It takes the main function as an argument and runs it when it finds a new sheet
PiScout(main)