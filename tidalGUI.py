
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
#from PIL import Image
import matplotlib
import matplotlib.dates as matdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.image as mpimg
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

#import urllib
import os
#import math
#from shutil import copyfile
import pickle
#import time
#import gc
from datetime import datetime, timedelta
import random
import argparse

import tidaldata as tidd

os.chdir('/home/ignace/Custom_Libraries/tidaldata/')
#%%

ap = argparse.ArgumentParser()
ap.add_argument('-d','--dataload', required=False, help = 'Already load a set of data.')
ap.add_argument('-D','--Dataload', required=False, help = 'Already load a set of data.')

args = vars(ap.parse_args())
dataload = args['dataload']
if args['Dataload']: dataload = args['Dataload']


class Main(QMainWindow):
# create a class with heritance from the QWidget object

    def __init__(self, dataload = None):
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
        logo = QIcon()
        im = QPixmap('support_files/Logo.png')
        im.setDevicePixelRatio(5)
        logo.addPixmap(im)
        self.setWindowIcon(logo)
        self.setGeometry(left,top,width, height)

        self.main_widget = MyTable(self, dataload = dataload)
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

    def __init__(self, parent, dataload = None):
        super(QWidget, self).__init__(parent)

        self.filenames = []
        self.tidedatasets = []
        self.plots = []
        self.peaks = []
        self.lows = []
        self.plotcolors =[[random.random(),random.random(),random.random()] for i in range(20)]
        self.scatters = []

        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
        #-------------- Make the input widges --------------#
        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#

        # ------------------------#
        # Main buttons ans inputs #
        # ------------------------#

        # Push button to load tidaldata object
        Load = QPushButton('Load .tid')
        Load.setFixedWidth(125)
        Load.clicked.connect(self.openLoadFileNameDialog)
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

        # checkbox to standardize data when uploading
        self.Standardize = QCheckBox('Standardize Data')
        self.Standardize.setChecked(False)
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
        self.canvas.mpl_connect('button_release_event', self.autoUpdateLims)
        self.canvas.mpl_connect('button_press_event', self.autoUpdateLims)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        # buttons to zoom and pan
        self.zoombut = QPushButton()
        self.zoombut.setCheckable(True)
        self.zoombut.setEnabled(False)
        im = QIcon('support_files/zoom_trans.png')
        self.zoombut.setIcon(im)
        self.zoombut.setDisabled(True)
        self.zoombut.clicked.connect(self.zoom)
        self.zoombut.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:checked {
            color: rgb(100,100,100,150);
            background-color: rgb(255, 128, 0);
            }
        """)

        self.panbut = QPushButton()
        self.panbut.setCheckable(True)
        self.panbut.setEnabled(False)
        im = QIcon('support_files/pan_trans.png')
        self.panbut.setIcon(im)
        self.panbut.setDisabled(True)
        self.panbut.clicked.connect(self.pan)
        self.panbut.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:checked {
            color: rgb(100,100,100,150);
            background-color: rgb(255, 128, 0);
            }
        """)

        self.homebut = QPushButton()
        self.homebut.setEnabled(False)
        im = QIcon('support_files/home_trans.png')
        self.homebut.setIcon(im)
        self.homebut.setDisabled(True)
        self.homebut.clicked.connect(self.home)
        self.homebut.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180,50);
            background-color: rgb(25, 25, 60, 0);
            }
        QPushButton:pressed {
            color: rgb(100,100,100,150);
            background-color: rgb(255, 128, 0);
            }
        """)

        # ------------#
        # table #
        # ------------#

        self.createTable()
        self.table_rows = 1

        # --------------#
        # table buttons #
        # --------------#

        self.SaveTable = QPushButton()
        self.SaveTable.setToolTip('Save the table content.')
        im = QIcon('support_files/save.png')
        self.SaveTable.setIcon(im)
        self.SaveTable.setDisabled(True)
        self.SaveTable.clicked.connect(self.saveTable)
        self.SaveTable.setFixedSize(25,25)
        self.SaveTable.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:pressed {
            color: rgb(100,100,100,150);
            background-color: rgb(25, 25, 25, 150);
            }
        """)

        self.LoadTable = QPushButton()
        self.LoadTable.setToolTip('Load previously saved table content.')
        im = QIcon('support_files/load.png')
        self.LoadTable.setIcon(im)
        self.LoadTable.clicked.connect(self.loadTable)
        self.LoadTable.setFixedSize(25,25)
        self.LoadTable.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:pressed {
            color: rgb(100,100,100,150);
            background-color: rgb(25, 25, 25, 150);
            }
        """)

        self.ClearTable = QPushButton()
        self.ClearTable.setToolTip('Clear table content.')
        im = QIcon('support_files/clear.png')
        self.ClearTable.setIcon(im)
        self.ClearTable.clicked.connect(self.clearTable)
        self.ClearTable.setFixedSize(25,25)
        self.ClearTable.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:pressed {
            color: rgb(100,100,100,150);
            background-color: rgb(25, 25, 25, 150);
            }
        """)

        self.ShowPeaks = QPushButton()
        self.ShowPeaks.setToolTip('Toggle view mode to peaks.')
        im = QIcon('support_files/ring.png')
        self.ShowPeaks.setIcon(im)
        self.ShowPeaks.setCheckable(True)
        self.ShowPeaks.clicked.connect(self.plotSeries)
        self.ShowPeaks.setFixedSize(25,25)
        self.ShowPeaks.setStyleSheet("""
        QPushButton {
            border-width: 25px solid white;
            border-radius: 0px;
            color: rgb(180,180,180);
            background-color: rgb(55, 55, 60, 0);
            }
        QPushButton:checked {
            border-style: outset;
            border-width: 1px;
            border-radius: 2px;
            border-color: rgb(50,50,50);
            color: rgb(100,100,100,150);
            background-color: rgb(55, 55, 60, 0);
            }
        """)


        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
        #-------------- Organize and set the layout --------------#
        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#

        self.grid = QGridLayout()

        grid_params = QGridLayout()
        grid_params.addWidget(Load, 0, 0)
        grid_params.addWidget(self.Standardize, 0, 1)
        grid_params.addWidget(start_time, 0, 2)
        grid_params.addWidget(self.start_time, 0, 3)
        grid_params.addWidget(end_time, 0, 4)
        grid_params.addWidget(self.end_time, 0, 5)

        grid_params.addWidget(ylim_top, 0, 7)
        grid_params.addWidget(self.ylim_top, 0, 8)
        grid_params.addWidget(ylim_bot, 0, 9)
        grid_params.addWidget(self.ylim_bot, 0, 10)

        canvas_but = QVBoxLayout()
        canvas_but.addWidget(self.zoombut)
        canvas_but.addWidget(self.panbut)
        canvas_but.addWidget(self.homebut)
        canvas_but.addStretch()

        table_but = QVBoxLayout()
        table_but.addWidget(self.SaveTable)
        table_but.addWidget(self.LoadTable)
        table_but.addWidget(self.ClearTable)
        table_but.addWidget(self.ShowPeaks)
        table_but.addStretch()

        self.grid.addLayout(grid_params, 0, 0, 1, 2)
        self.grid.addWidget(self.canvas, 1, 0, 1, 1)
        self.grid.addWidget(self.Table, 2, 0)
        self.grid.addLayout(table_but, 2, 1)
        self.grid.addLayout(canvas_but, 1, 1)

        self.setLayout(self.grid)

        self.show()

        # load datasets if flag is given
        if dataload: self.loadDefaultData(dataload)

        #-------------------------------------#
        #-------------- Methods --------------#
        #-------------------------------------#

    def openLoadFileNameDialog(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","*.tid", options=options)
        print('Loading file...')

        if filename:
            self.addSeries(filename)

    def createTable(self):
        """
        Method to initiate the table (set columns and column names)
        """

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
        self.Table.setColumnCount(2)
        self.Table.setHorizontalHeaderLabels(['Name TideData','Tidal Range (m)'])

        self.Table.setItem(0,0, QTableWidgetItem("Name"))

        #Table will fit the screen horizontally
        [self.Table.setColumnWidth(i, 350) for i in range(0,2)]
        self.Table.horizontalHeader().setSectionResizeMode(0,
            QHeaderView.Stretch)

    def initPlot(self):
        """
        Method to initiate the plot (draw axes, set labels, etc.)
        """
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

    def addSeries(self, filename):
        """
        Method to add a series to the table and to plot the series on the plot.

        args:
            filename: (Required) Directory path string of the recently loaded TideData object
        """

        # load the TideData object and add to the attributed list
        # add filename path to attributed list
        # set row count of table
        td = tidd.TideData.load(filename)
        if self.Standardize.isChecked():
            td.standardize()
        self.tidedatasets.append(td)
        self.filenames.append(filename)
        self.Table.setRowCount(self.table_rows)

        # set the name and range of the TideData object in the table
        item = QTableWidgetItem(td.name)
        item.setFlags(Qt.ItemIsEnabled)
        self.Table.setItem(self.table_rows - 1, 0, item)
        item = QTableWidgetItem('%.2f' % td.tide_range)
        item.setFlags(Qt.ItemIsEnabled)
        self.Table.setItem(self.table_rows - 1, 1, item)

        """
        # fill in zero for all shifts
        for i in range(2,6):
            item = QTableWidgetItem(str(0))
            item.setForeground(QColor(180, 180, 180))
            self.Table.setItem(self.table_rows - 1, i, item)
        """

        # add the series to the table
        color = self.plotcolors[self.table_rows - 1]
        color = qRgb(255*color[0], 255*color[1], 255*color[2])
        item = self.Table.item(self.table_rows - 1, 0)
        item.setForeground(QColor(color))
        item = self.Table.item(self.table_rows - 1, 1)
        item.setForeground(QColor(color))

        # update attributes
        self.table_rows += 1

        # update all limits and make the table reactive
        #self.Table.cellChanged.connect(self.updateShifts)

        # enable load and save button
        self.SaveTable.setEnabled(True)

        # update canvas
        self.ax.plot(td.times, td.tides)
        self.autoUpdateLims(0)
        self.plotSeries()

        # enable buttons
        self.zoombut.setEnabled(True)
        self.panbut.setEnabled(True)
        self.homebut.setEnabled(True)

    def autoUpdateLims(self,_):
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

    def plotSeries(self):

        self.ax.clear()
        self.ax.grid('on')
        self.ax.set_ylabel('Water Level [m]', fontweight = 'bold', fontsize = 9)

        self.scatters = []
        self.plots = []

        if self.ShowPeaks.isChecked():

            if len(self.peaks) < len(self.tidedatasets):
                for td in self.tidedatasets:
                    # calculate peaks and lows
                    pt, pwl = td.getPeaks()
                    lt, lwl = td.getLows()
                    self.peaks.append([pt, pwl])
                    self.lows.append([lt, lwl])

            for i in range(len(self.tidedatasets)):
                td = self.tidedatasets[i]

                color = self.plotcolors[i]
                print(color)
                color_transp = color[:7] + [0.33]
                self.plots.append(self.ax.plot(td.times, td.tides, color = color_transp))

                pt, pwl = self.peaks[i]
                lt, lwl = self.lows[i]

                self.scatters.append([self.ax.plot(pt, pwl, linestyle = 'None', marker = 'o', mec = color, mfc = '#ffffff00', mew = 0.5),
                    self.ax.plot(lt, lwl, linestyle = 'None', marker = 'o', mec = color, mfc = '#ffffff00', mew = 0.5)])


        else:
            for i in range(len(self.tidedatasets)):

                td = self.tidedatasets[i]
                color = self.plotcolors[i]
                self.plots.append(self.ax.plot(td.times, td.tides, c = color, label = td.name))

        self.updateLims()

        #for i in range(self.table_rows):
        #    self.updateShifts(i, 2)

    def clearTable(self):
        self.Table.clearContents()
        self.Table.setRowCount(1)

        self.plots = []
        self.tidedatasets = []
        self.filenames = []
        self.peaks = []
        self.lows = []
        self.scatters = []

        self.table_rows = 1

        self.ax.clear()
        self.ax.grid('on')
        self.canvas.draw()

    def saveTable(self):
        options = QFileDialog.Options()
        fn, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;tdgui Files (*.tdgui)", options=options)

        if fn:
            if fn[-6:] != '.tdgui': fn += '.tdgui'
            shifts = np.zeros([self.table_rows-1, 4])
            for j in range(2,6):
                for i in range(self.table_rows-1):

                    it = float(self.Table.item(i, j).text())
                    shifts[i,j-2] = it

            save_object = {'filenames': self.filenames, 'shifts': shifts}

            pickle.dump(save_object, open(fn, "wb" ))

    def loadTable(self):
        options = QFileDialog.Options()
        fn, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","*.tdgui", options=options)

        if fn:
            print('Loading table...')
            load_object = pickle.load(open( fn, "rb" ))
            filenames = load_object['filenames']
            shifts = load_object['shifts']

            self.clearTable()
            self.filenames = filenames

            for i in range(len(self.filenames)):
                self.addSeries(self.filenames[i])

                """            for i in range(self.table_rows-1):
                for j in range(2,6):
                    it = QTableWidgetItem(str(shifts[i,j-2]))
                    it = self.Table.setItem(i, j, it)"""

            self.plotSeries()

            print('Ready!')

    def home(self):
            self.toolbar.home()
            self.autoUpdateLims(0)

    def zoom(self):
        if self.zoombut.isChecked():
            self.toolbar.zoom()
            self.panbut.setChecked(False)
        else:
            self.toolbar.zoom(False)

    def pan(self):
        if self.panbut.isChecked():
            self.toolbar.pan()
            self.zoombut.setChecked(False)
        else:
            self.toolbar.zoom(False)

    def loadDefaultData(self, dataload):
        if dataload.upper() == 'JDN' or 'JAN' in dataload.upper():
            dir = '/home/ignace/Documents/PhD/Data/Tide_Gauge_Data/After2017/TideDataSets/JanDeNul/'
        elif 'INOCAR' in dataload.upper() and 'BEFORE' in dataload.upper():
            dir = '/home/ignace/Documents/PhD/Data/Tide_Gauge_Data/Before2017/TideDataSets/INOCAR/'
        elif 'INOCAR' in dataload.upper():
            dir = '/home/ignace/Documents/PhD/Data/Tide_Gauge_Data/Before2017/TideDataSets/INOCAR/'
        elif 'SLA' in dataload.upper():
            dir = '/home/ignace/Documents/PhD/Data/El-Niño/SLA/TideDataSets/'
        else:
            dir = None

        if dir:
            for file in os.listdir(dir):
                if file.endswith('.tid'):
                    print(f'Loading {file}...')
                    self.addSeries(dir + file)
            print('All datasets are loaded!')
        else: print('dataload argument not recognised!')



#--------------------------------------------------------------------#
# Execute the program

app = QApplication([])
window = Main(dataload = dataload)
window.show()
app.exec_()
