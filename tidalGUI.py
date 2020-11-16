
"""
Created on Wed Oct 17 17:20:50 2018

@author: ignace
"""

# programm which asks long and lat and zoom level
#%%

#%%
import sys
import PyQt5.QtCore
from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
import numpy as np
from PIL import Image
import matplotlib.dates as matdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.image as mpimg
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import urllib
import os
import math
from shutil import copyfile
import pickle
import time
import gc
from datetime import datetime, timedelta
import random

import tidaldata as tidd



os.chdir('/home/ignace/Custom_Libraries/t2viewer/')
#%%


class Main(QMainWindow):
# create a class with heritance from the QWidget object

    def __init__(self):
        # assign attributes
        super().__init__()
        # return the parent class from this child class and calls its constructor (constructor = special kind of method to initialize any instance variables (assigning attributes to it))

        title = "Tidal Data Visualization"
        left = 2000
        top = 100
        width = 1250
        height = 600

        self.clickcount = 0
        self.F = np.zeros([500,500])

        self.setWindowTitle(title)
        #self.setWindowIcon(QIcon('support_files/logo.png'))
        self.setGeometry(left,top,width, height)

        self.main_widget = MyTable(self)
        self.setCentralWidget(self.main_widget)

        self.setStyleSheet("""
        QWidget {
            background-color: rgb(35, 35, 35);
            }
        """)

        self.main_widget.setStyleSheet("""
        QWidget {
            background-color: rgb(45, 45, 45);
            }
        """)

        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

class MyTable(QWidget):

    sig = pyqtSignal(list)
    sigload = pyqtSignal(list)

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.filenames = []
        self.tidedatasets = []
        self.plots = []

        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
        #-------------- Make the input widges --------------#
        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#

        # ------------------------#
        # Main buttons ans inputs #
        # ------------------------#

        # Push button to load tidaldata object
        Load = QPushButton('Load .tid')
        Load.setFixedWidth(125)
        Load.clicked.connect(self.openFileNameDialog)
        Load.setToolTip('Load the output from a TELEMAC 2D simulation')
        Load.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 5px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60);
            min-height: 40px;
            }
        QPushButton:pressed {
            color: rgb(120,120,120);
            background-color: rgb(75, 75, 80);
            }
        """)


        # Push button to clear all tidaldata objects
        Clear = QPushButton('Clear all')
        Clear.setFixedWidth(125)
        Clear.clicked.connect(self.clearTable)
        Clear.setToolTip('Load the output from a TELEMAC 2D simulation')
        Clear.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 5px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60);
            min-height: 40px;
            }
        QPushButton:pressed {
            color: rgb(120,120,120);
            background-color: rgb(75, 75, 80);
            }
        """)

        # checkbox to standardize data when uploading
        self.Standardize = QCheckBox('Standardize Data')
        self.Standardize.setChecked(True)
        self.Standardize.setStyleSheet("""
            QCheckBox {
            color: rgb(180,180,180);
            background-color: rgb(35,35,35);
            }""")

        # date and time
        start_time = QLabel('Start Date & Time:')
        start_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        start_time.setStyleSheet("""
            QLabel {
            color: rgb(180,180,180);
            background-color: rgb(35, 35, 35);
            }""")
        end_time = QLabel('End Date & Time:')
        end_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        end_time.setStyleSheet("""
            QLabel {
            color: rgb(180,180,180);
            background-color: rgb(35, 35, 35);
            }""")

        self.start_time = QLineEdit()
        self.start_time.setFixedWidth(150)
        self.start_time.editingFinished.connect(self.updateLims)
        self.start_time.setStyleSheet("""
        QLineEdit {
        color: rgb(180,180,180);
        background-color: rgb(25,25,25);
        }""")
        self.end_time = QLineEdit()
        self.end_time.setFixedWidth(150)
        self.end_time.editingFinished.connect(self.updateLims)
        self.end_time.setStyleSheet("""
        QLineEdit {
        color: rgb(180,180,180);
        background-color: rgb(25,25,25);
        }""")

        # y limit controls
        ylim_top = QLabel('Top:')
        ylim_top.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ylim_top.setStyleSheet("""
            QLabel {
            color: rgb(180,180,180);
            background-color: rgb(35, 35, 35);
            }""")
        ylim_bot = QLabel('Bottom:')
        ylim_bot.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ylim_bot.setStyleSheet("""
            QLabel {
            color: rgb(180,180,180);
            background-color: rgb(35, 35, 35);
            }""")

        self.ylim_top = QDoubleSpinBox()
        self.ylim_top.setDecimals(2)
        self.ylim_top.setRange(-1e5,1e5)
        self.ylim_top.setSuffix(' m')
        self.ylim_top.setFixedWidth(150)
        self.ylim_top.editingFinished.connect(self.updateLims)
        self.ylim_top.setStyleSheet("""
        QDoubleSpinBox {
        color: rgb(180,180,180);
        background-color: rgb(25,25,25);
        }""")
        self.ylim_bot = QDoubleSpinBox()
        self.ylim_bot.setDecimals(2)
        self.ylim_bot.setRange(-1e5,1e5)
        self.ylim_bot.setSuffix(' m')
        self.ylim_bot.setFixedWidth(150)
        self.ylim_bot.editingFinished.connect(self.updateLims)
        self.ylim_bot.setStyleSheet("""
        QDoubleSpinBox {
        color: rgb(180,180,180);
        background-color: rgb(25,25,25);
        }""")

        # ------------#
        # Time Series #
        # ------------#

        # FigureCanvas to show the mesh in
        self.figure = plt.figure()
        self.figure.set_facecolor((45/255, 45/255, 45/255))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedHeight(350)
        self.initPlot()

        # ------------#
        # table #
        # ------------#

        self.createTable()
        self.table_rows = 1

        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
        #-------------- Organize and set the layout --------------#
        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#

        self.grid = QGridLayout()

        grid_params = QGridLayout()
        grid_params.addWidget(Load, 0, 0)
        grid_params.addWidget(Clear, 0, 1)
        grid_params.addWidget(self.Standardize, 0, 2)
        grid_params.addWidget(start_time, 0, 3)
        grid_params.addWidget(self.start_time, 0, 4)
        grid_params.addWidget(end_time, 0, 5)
        grid_params.addWidget(self.end_time, 0, 6)

        grid_params.addWidget(ylim_top, 0, 7)
        grid_params.addWidget(self.ylim_top, 0, 8)
        grid_params.addWidget(ylim_bot, 0, 9)
        grid_params.addWidget(self.ylim_bot, 0, 10)

        self.grid.addLayout(grid_params, 0, 0)
        self.grid.addWidget(self.canvas, 1, 0)
        self.grid.addWidget(self.Table, 2, 0)

        self.setLayout(self.grid)

        self.show()

        #-------------------------------------#
        #-------------- Methods --------------#
        #-------------------------------------#

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","*.tid", options=options)
        print('Loading file...')

        if filename:

            td = tidd.TideData.load(filename)
            if self.Standardize.isChecked():
                td.standardize()
            self.tidedatasets.append(td)

            self.filenames.append(filename)
            self.Table.setRowCount(self.table_rows)

            item = QTableWidgetItem(td.name)
            item.setFlags(Qt.ItemIsEnabled)
            self.Table.setItem(self.table_rows - 1, 0, item)
            item = QTableWidgetItem('%.2f' % td.tide_range)
            item.setFlags(Qt.ItemIsEnabled)
            self.Table.setItem(self.table_rows - 1, 1, item)

            for i in range(2,6):
                item = QTableWidgetItem(str(0))
                item.setForeground(QColor(180, 180, 180))
                self.Table.setItem(self.table_rows - 1, i, item)

            self.addSeries()
            self.table_rows += 1

    def createTable(self):
        self.Table = QTableWidget()
        self.Table.setStyleSheet("""
        QTableWidget {
            color: rgb(180,180,180);
        }
        QHeaderView:section {
        color:rgb(180,180,180);
        }
        """)

        #Row count
        self.Table.setRowCount(1)

        #Column count
        self.Table.setColumnCount(6)
        self.Table.setHorizontalHeaderLabels(['Name TideData','Tidal Range (m)','Vertical shift (m)','Time shift (hr)', 'Time shift (min)', 'Time shift (s)'])

        self.Table.setItem(0,0, QTableWidgetItem("Name"))

        #Table will fit the screen horizontally
        [self.Table.setColumnWidth(i, 150) for i in range(1,6)]
        self.Table.horizontalHeader().setSectionResizeMode(0,
            QHeaderView.Stretch)



    def initPlot(self):
        self.figure.subplots_adjust(left = 0.1, right = 0.94, bottom = 0.1, top = 0.9)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor((45/255, 45/255, 45/255))

        broken_white = (150/255, 150/255, 150/255)
        self.ax.grid('on', color = broken_white)
        self.ax.spines['bottom'].set_color(broken_white)
        self.ax.spines['top'].set_color(broken_white)
        self.ax.spines['right'].set_color(broken_white)
        self.ax.spines['left'].set_color(broken_white)
        self.ax.tick_params(axis='x', colors=broken_white, labelsize = 7)
        self.ax.tick_params(axis='y', colors=broken_white, labelsize = 7)
        self.ax.xaxis.label.set_color(broken_white)
        self.ax.yaxis.label.set_color(broken_white)

        self.ax.set_ylabel('Water Level [m]', fontweight = 'bold', fontsize = 9)

    def addSeries(self):
        td = self.tidedatasets[-1]
        plot = self.ax.plot(td.times, td.tides, label = td.name)
        color = plot[-1].get_color()
        item = self.Table.item(self.table_rows - 1, 0)
        item.setForeground(QColor(color))
        item = self.Table.item(self.table_rows - 1, 1)
        item.setForeground(QColor(color))

        self.canvas.draw()

        self.plots.append(plot)

        self.autoUpdateLims()
        self.Table.cellChanged.connect(self.updateShifts)

    def autoUpdateLims(self):
        t0,t1 = self.ax.get_xlim()

        t0 = matdates.num2date(t0)
        t1 = matdates.num2date(t1)

        t0_str = "%d-%d-%d %d:%d:%d" % (t0.year, t0.month, t0.day, t0.hour, t0.minute, t0.second)
        t1_str = "%d-%d-%d %d:%d:%d" % (t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)

        self.start_time.setText(t0_str)
        self.end_time.setText(t1_str)

        y0, y1 = self.ax.get_ylim()
        self.ylim_top.setValue(y1)
        self.ylim_bot.setValue(y0)

    def updateLims(self):
        t0_str = self.start_time.text()
        t1_str = self.end_time.text()

        t0_str = t0_str.split(' ')
        t0_year, t0_month, t0_day = [int(i) for i in t0_str[0].split('-')]
        t0_hr, t0_min, t0_sec = [int(i) for i in t0_str[1].split(':')]
        t0 = datetime(t0_year, t0_month, t0_day, t0_hr, t0_min, t0_sec)

        t1_str = t1_str.split(' ')
        t1_year, t1_month, t1_day = [int(i) for i in t1_str[0].split('-')]
        t1_hr, t1_min, t1_sec = [int(i) for i in t1_str[1].split(':')]
        t1 = datetime(t1_year, t1_month, t1_day, t1_hr, t1_min, t1_sec)

        self.ax.set_xlim(matdates.date2num(t0), matdates.date2num(t1))
        self.ax.set_ylim(self.ylim_bot.value(), self.ylim_top.value())
        self.canvas.draw()

    def updateShifts(self, row, col):
        try:
            if col >= 2 and len(self.plots) > 0:

                td = self.tidedatasets[row]
                times_upd, tides_upd = td.times.copy(), td.tides.copy()

                tides_upd += float(self.Table.item(row, 2).text())
                hr = float(self.Table.item(row, 3).text())
                min = float(self.Table.item(row, 4).text())
                sec = float(self.Table.item(row, 5).text())
                times_upd = [(t + timedelta(seconds = hr*3600 + min*60 + sec)) for t in times_upd]

                self.plots[row][-1].set_data(times_upd, tides_upd)
                self.canvas.draw()
        except:
            pass

    def clearTable(self):
        self.Table.clearContents()
        self.Table.setRowCount(1)
        self.plots = []
        self.ax.clear()
        self.ax.grid('on')
        self.canvas.draw()





#--------------------------------------------------------------------#
# Execute the program

app = QApplication([])
window = Main()
window.show()
app.exec_()