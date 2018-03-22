import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from time import sleep
import ctypes
import requests
import server
from threading import Thread
import csv
from server import CURRENT_EVENT
import sqlite3 as sql

# PiScout is a means of collecting match data in a scantron-like format
# This program was designed to be easily configurable, and new sheets can be made rapidly
# The configuration for the sheets is done in a separate file (main.py)
# Kaitlyn Sandor 2018
class PiScout:
    # Firstly, initializes the fields of a PiScout object
    # Then it starts the main loop of PiScout
    # Requires a function "main" which contains the sheet configuration
    # Loops indefinitely and triggers a response whenever a new sheet is added

    def __init__(self, main):
        print('PiScout Starting')
        self.sheet = None;
        self.display = None;
        self.data = []
        self.labels = ["Team", "Match", "Auto Switch", "Auto Scale", "Auto Exchange", "Auto Dropped", "Auto Cross",
                       "Tele Switch", "Tele Scale", "Tele Exchange", "Tele Dropped", "Tele Opp Switch", "Climb", "Ramp",
                       "Climbed a Robot", "Defense", "Defended", "Notes"]
        Thread(target=server.start).start()  # local database server
        f = set(os.listdir("Files"))
        while True:
            sleep(0.25)
            files = set(os.listdir("Files"))  # grabs all file names as a set
            added = files - f  # check if any files were added (if first iteration, added = files)
            f = files  # will hold onto this value for the next iteration
            for file in added:
                if '.txt' in file:
                    main(self, file)

    # Adds a data entry into the data dictionary
    def set(self, contents):
        self.data.append(contents)
    # Opens the GUI, preparing the data for submission

    def submit(self):
        print(self.data)
        if self.data[1] == 0:
            print("Found an empty match, skipping")
            self.data = []
            return

        datapath = 'data_' + CURRENT_EVENT + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        history = cursor.execute('SELECT * FROM scout WHERE d0=? AND d1=?',
                                 (str(self.data[0]), str(self.data[1]))).fetchall()
        if history:
            print("Already processed this match, skipping")
            self.data = []
            self.labels = []
            return

        # the following block opens the GUI for piscout, this code shouldn't need to change
        print("Found a new file, opening")
        output = ''
        self.labels = ["Team", "Match", "Auto Switch", "Auto Scale", "Auto Exchange", "Auto Dropped", "Auto Cross",
                  "Tele Switch", "Tele Scale", "Tele Exchange", "Tele Dropped", "Tele Opp Switch", "Climb", "Ramp",
                  "Climbed a Robot", "Defense", "Defended", "Notes"]
        print(len(self.labels))
        print(len(self.data))
        assert len(self.labels) == len(self.data)
        for a in range(len(self.data)):
            output += self.labels[a] + "=" + str(self.data[a]) + '\n'
        self.save(CURRENT_EVENT)
        # fig = plt.figure('PiScout')
        # fig.subplots_adjust(left=0, right=.1)
        # plt.subplot(111)
        # #plt.imshow(self.display)
        # plt.title('File')
        # plt.text(600, 784, output, fontsize=12)
        # upload = Button(plt.axes([0.68, 0.31, 0.15, 0.07]), 'Upload Data')
        # upload.on_clicked(self.upload)
        # save = Button(plt.axes([0.68, 0.24, 0.15, 0.07]), 'Save Data Offline')
        # save.on_clicked(self.save)
        # edit = Button(plt.axes([0.68, 0.17, 0.15, 0.07]), 'Edit Data')
        # edit.on_clicked(self.edit)
        # cancel = Button(plt.axes([0.68, 0.1, 0.15, 0.07]), 'Cancel')
        # cancel.on_clicked(self.cancel)
        # mng = plt.get_current_fig_manager()
        # try:
        #     mng.window.state('zoomed')
        # except AttributeError:
        #     print("Window resizing exploded, oh well.")
        # plt.show()
        self.data = []
        self.labels = []

    # Invoked by the "Save Data Offline" button
    # Adds data to a queue to be uploaded online at a later time
    # Also stores in the local database
    def save(self, event):
        print("Queueing match for upload later")
        with open("queue.txt", "a+") as file:
            file.write(str(self.data) + '\n')
        plt.close()
        requests.post("http://127.0.0.1:8000/submit", data={'event': server.CURRENT_EVENT, 'data': str(self.data)})

    # Invoked by the "Upload Data" button
    # Uploads all data (including queue) to the online database
    # Uploads a copy to the local database as backup
    def upload(self, event):
        plt.close()
        print("Attempting upload to server")

        try:  # post it to piscout's ip address
            requests.post("http://34.225.109.159/submit", data={'data': str(self.data)})
            print("Uploading this match was successful")
            if os.path.isfile('queue.txt'):
                with open("queue.txt", "r") as file:
                    for line in file:
                        requests.post("http://34.225.109.159/submit", data={'event': server.CURRENT_EVENT, 'data': line})
                        print("Uploaded an entry from the queue")
                os.remove('queue.txt')
            requests.post("http://127.0.0.1:8000/submit", data={'event': server.CURRENT_EVENT, 'data': str(self.data)})
        except:
            print("Failed miserably")
            r = self.message("Upload Failed",
                             'Upload failed. Retry? Otherwise, data will be stored in the queue for upload later.',
                             type=5)
            if r == 4:
                self.upload(event)
            else:
                self.save(event)

    # Invoked by the "Edit Data" button
    # Opens up the data in notepad, and lets the user make modifications
    # Afterward, it re-opens the GUI with the updated data
    def edit(self, event):
        with open('history.txt', 'r') as file:
            lines = file.readlines()
            lines = lines[:-1]
        with open('history.txt', 'w+') as file:
            file.writelines(lines)
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
        with open('history.txt', 'r') as file:
            lines = file.readlines()
            lines = lines[:-1]
        with open('history.txt', 'w+') as file:
            file.writelines(lines)

    # Displays a message box
    def message(self, title, message, type=0):
        return ctypes.windll.user32.MessageBoxW(0, message, title, type)