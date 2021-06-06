'''
    * File:     program.py
    * Coded by: Ricky Dodd
    A GUI interface programmed for a Raspberry Pi 3 Model B+.
'''

import sys
import time
import subprocess
import _thread
import json
import RPi.GPIO as GPIO
from PySide import QtGui, QtCore
import plantbuddy as pb

PUMP_PHYS_PIN    = 16
TH_DATA_PHYS_PIN = 7 # temperature and relative humidity data pin

soil_moisture, water_level = None, None

class App(QtGui.QWidget):
    def __init__(self):
        super(App, self).__init__()
        self.buddy = pb.PlantBuddy()
        self.__emailAddress = None
        self.initUI()
        self.initEvents()
    
    def initUI(self):
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setGeometry(300, 300, 250, 250)
        self.tabWidget.setWindowTitle("Plant Buddy")

        # Establishing Control Panel Widgets
        controlPanelWidget = QtGui.QWidget()
        self.waterButton = QtGui.QPushButton("Water")
        self.waterLabel = QtGui.QLabel("Watering session: IDLE")
        self.emailLabel = QtGui.QLabel("Enter e-mail:")
        self.emailField = QtGui.QLineEdit()
        self.emailButton = QtGui.QPushButton("Set")
        
        # Establishing Metric Widgets
        metricsWidget = QtGui.QWidget()
        self.soilMoistureLabel = QtGui.QLabel("Soil moisture level:")
        self.soilMoistureValue = QtGui.QLabel("PLEASE WAIT")
        self.tempLabel = QtGui.QLabel("Temperature (C):")
        self.tempValue = QtGui.QLabel("PLEASE WAIT")
        self.humLabel = QtGui.QLabel("Relative humidity:")
        self.humValue = QtGui.QLabel("PLEASE WAIT")
        self.waterLevelLabel = QtGui.QLabel("Water Level:")
        self.waterLevelValue = QtGui.QLabel("PLEASE WAIT")
        self.emailReport = QtGui.QPushButton("E-Mail Report")
        
        # Laying Out Control Panel Widgets
        self.controlLayout = QtGui.QGridLayout(controlPanelWidget)
        self.controlLayout.addWidget(self.waterButton)
        self.controlLayout.addWidget(self.waterLabel)
        self.controlLayout.addWidget(self.emailLabel)
        self.controlLayout.addWidget(self.emailField)
        self.controlLayout.addWidget(self.emailButton)
        
        # Laying Out Metric Widgets
        self.metricsLayout = QtGui.QGridLayout(metricsWidget)
        self.metricsLayout.addWidget(self.soilMoistureLabel)
        self.metricsLayout.addWidget(self.soilMoistureValue)
        self.metricsLayout.addWidget(self.tempLabel)
        self.metricsLayout.addWidget(self.tempValue)
        self.metricsLayout.addWidget(self.humLabel)
        self.metricsLayout.addWidget(self.humValue)
        self.metricsLayout.addWidget(self.waterLevelLabel)
        self.metricsLayout.addWidget(self.waterLevelValue)
        self.metricsLayout.addWidget(self.emailReport)

        self.tabWidget.addTab(controlPanelWidget, "Control Panel")
        self.tabWidget.addTab(metricsWidget, "Metrics")
        
        self.tabWidget.show()
    
    def initEvents(self):
        '''
            connecting buttons to events
        '''
        self.waterButton.clicked.connect(self.water)
        self.emailButton.clicked.connect(self.setEmail)
        self.emailReport.clicked.connect(self.sendReport)
    
    # Events
    def water(self):
        '''
            inits two threads
            Pump-thread handles the pumping itself
            Pumping-check-thread keeps the GUI updated about pumping
        '''
        try:
            _thread.start_new_thread(self.buddy.pump, ("Pump-thread", 0))
            _thread.start_new_thread(self.setPumpingActive, ("Pumping-check-thread", 0))
        except:
            return
        
    def setEmail(self):
        self.__emailAddress = self.emailField.text()
        print(self.__emailAddress)

    def sendReport(self):
        if self.__emailAddress is not None:
            self.buddy.sendReport(str(self.__emailAddress))
        else:
            reply = QtGui.QMessageBox()
            reply.setWindowTitle("Error!")
            reply.setText("You must set an e-mail address.")
            reply.exec_()
    
    def setPumpingActive(self, _, __):
        while True:
            if self.buddy.getIsPumping():
                t_end = time.time() + self.buddy.getTimeConstant()
                while time.time() < t_end:
                    self.waterLabel.setText("Watering session: ACTIVE")
                self.waterLabel.setText("Watering session: IDLE")
        
    def updateMetrics(self, _, __):
        '''
            updates the metrics values, has an initial delay in seconds
        '''
        while True:
            soilMoisture, temp, hum, waterLevel = self.buddy.getState()
            if soilMoisture is not None:
                self.soilMoistureValue.setText(str(soilMoisture))
            if temp is not None:
                self.tempValue.setText(str(temp))
            if hum is not None:
                self.humValue.setText(str(hum))
            if waterLevel is not None:
                self.waterLevelValue.setText(str(waterLevel))
        
        
    def moistureSubscription(self, _, __):
        i = 0 # counter to prevent operating on first two lines
        process = subprocess.Popen(["particle", "subscribe", "soil_moisture"],
                                   stdout = subprocess.PIPE)
        for line in iter(process.stdout.readline, b''):
            if i >= 2:
                data = json.loads(line.decode("utf-8"))["data"] # decoding from byte to utf-8, then turning from json to dict
                innerData = json.loads(data)
                soilMoisture = int(innerData["data"])
                self.buddy.setSoilMoisture(soilMoisture)
            i += 1
        process.stdout.close()
        process.wait()
    
    def waterLevelSubscription(self, _, __):
        i = 0 # counter to prevent operating on first two lines
        process = subprocess.Popen(["particle", "subscribe", "water_level"],
                                   stdout = subprocess.PIPE)
        for line in iter(process.stdout.readline, b''):
            if i >= 2:
                data = json.loads(line.decode("utf-8"))["data"] # decoding from byte to utf-8, then turning from json to dict
                innerData = json.loads(data)
                waterLevel = float(innerData["data"])
                self.buddy.setWaterLevel(waterLevel)
                if self.buddy.getWaterLevel() > self.buddy.getCritical():
                    self.buddy.sendCriticalWarning(self.__emailAddress)
                elif self.buddy.getWaterLevel() > self.buddy.getWarning():
                    self.buddy.sendWarning(self.__emailAddress)
            i += 1
        process.stdout.close()
        process.wait()

def main():
    app = QtGui.QApplication(sys.argv)
    ex = App()

    try:
        _thread.start_new_thread(ex.buddy.keepTime, ("Time-thread", 0))
        _thread.start_new_thread(ex.moistureSubscription, ("Moisture-thread", 0))
        _thread.start_new_thread(ex.waterLevelSubscription, ("Water-level-thread", 0))
        _thread.start_new_thread(ex.buddy.updateStateLoop, ("Update-state-thread", 0))
        _thread.start_new_thread(ex.updateMetrics, ("Update-metrics-thread", 0))
        _thread.start_new_thread(ex.buddy.resetEmailStatus, ("Reset-email-status-thread", 0))
    except:
        print("Threads closed.")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
