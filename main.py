from piscout import *


# Main method to process a full-page sheet
# Submits three times, because there are three matches on one sheet
def main(scout, file):
    with open('Files/' + file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parsed = parse(scout, line)
            for i in range (len(parsed)):
                scout.set(parsed[i])
            scout.submit()
def parse(scout, text):
    char = ''
    i = 0
    s = ""
    parsed = []
    while i in range (len(text)):
        char = text[i]
        if(char != '[' and char != ',' and char != ']'):
            s+= char
        elif(char == ',' or char == ']'):
            parsed.append(s)
            s = ""
        i+=1
    return parsed
# This line creates a new PiScout and starts the program
# It takes the main function as an argument and runs it when it finds a new sheet
PiScout(main)
