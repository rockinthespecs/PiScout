from piscout import *
import csv
# Main method to process a full-page sheet
# Submits three times, because there are three matches on one sheet
def main(scout, file):
    with open(file + ".csv", 'rt', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            scout.set(row)
    # f = open(file + '.csv')
    # csvf = csv.reader(f)
    # for row in csvf:
    #     scout.set(row)
    # scout.submit()
    #trans = ""
    #perc = np.empty((0, 16))
    # remember that letters actually start on te second row
# This line creates a new PiScout and starts the program
# It takes the main function as an argument and runs it when it finds a new sheet
PiScout(main)