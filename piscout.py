import cv2
import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from time import sleep
import ctypes
import requests
from threading import Thread
import sqlite3 as sql
from event import CURRENT_EVENT

# PiScout is a means of collecting match data in a scantron-like format
# This program was designed to be easily configurable, and new sheets can be made rapidly
# The configuration for the sheets is done in a separate file (main.py)
# Cory Lynch 2015
class main:
    # Firstly, initializes the fields of a PiScout object
    # Then it starts the main loop of PiScout
    # Requires a function "main" which contains the sheet configuration
    # Loops indefinitely and triggers a response whenever a new sheet is added
    def __init__(self):
        print('PiScout Starting')
        self.data = []
        self.labels = []
        self.shift = 0

        f = set(os.listdir("Sheets"))
        while True:
            sleep(0.25)
            files = set(os.listdir("Data")) #grabs all file names as a set
            added = files - f #check if any files were added (if first iteration, added = files)
            for file in added:
                if '.txt' in file :
                    retval = self.loadsheet("Sheets/" + file)
                    if retval == 1:
                        #main(self) #call the main loop with this PiScout object as an argument
                        f.add(file)
                    elif retval == -1:
                        f.add(file)
    # Invoked by the "Save Data Offline" button
    # Adds data to a queue to be uploaded online at a later time
    # Also stores in the local database
    def save(self, event):
        print("Queueing match for upload later")
        with open("queue.txt", "a+") as file:
            file.write(str(self.data) + '\n')
        plt.close()
        requests.post("http://127.0.0.1:8000/submit", data={'event':CURRENT_EVENT, 'data': str(self.data)})

    # Invoked by the "Upload Data" button
    # Uploads all data (including queue) to the online database
    # Uploads a copy to the local database as backup
    def upload(self, event):
        plt.close()
        print("Attempting upload to server")

        try: #post it to piscout's ip address
            requests.post("http://34.199.157.169/submit", data={'event':CURRENT_EVENT, 'data': str(self.data)})
            print("Uploading this match was successful")
            if os.path.isfile('queue.txt'):
                with open("queue.txt", "r") as file:
                    for line in file:
                        #requests.post("http://34.199.157.169/submit", data={'event':CURRENT_EVENT, 'data': line})
                        print("Uploaded an entry from the queue")
                os.remove('queue.txt')
            requests.post("http://127.0.0.1:8000/submit", data={'event':CURRENT_EVENT, 'data': str(self.data)})
        except:
            print("Failed miserably")
            r = self.message("Upload Failed", 'Upload failed. Retry? Otherwise, data will be stored in the queue for upload later.', type=5)
            if r == 4:
                self.upload(event)
            else:
                self.save(event)

    # Invoked by the "Edit Data" button
    # Opens up the data in notepad, and lets the user make modifications
    # Afterward, it re-opens the GUI with the updated data
    def edit(self, event):
        datastr = ''
        for a in range(len(self.data)):
            datastr += self.labels[a] + "=" + str(self.data[a]) + '\n'
        with open('piscout.txt', "w") as file:
            file.write(datastr)
        os.system('piscout.txt')
        try:
            d = []
            with open('piscout.txt', 'r') as file:
                for line in file:
                    d.append(int(line.split('=')[1].replace('\n', '')))
            self.data = d
        except:
            self.message("Malformed Data", "You messed something up; the data couldn't be read. Try again.")
        plt.close()
        self.submit()

    # Invoked by the "Cancel" button
    # Closes the GUI and erases the entry from the history file
    def cancel(self, event):
        plt.close()

    # Displays a message box
    def message(self, title, message, type=0):
        return ctypes.windll.user32.MessageBoxW(0, message, title, type)