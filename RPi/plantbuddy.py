import time
import subprocess
import RPi.GPIO as GPIO
import Adafruit_DHT
import json

PUMP_PHYS_PIN    = 16
TH_DATA_PHYS_PIN = 7 # temperature and relative humidity data pin

DHT_SENSOR = Adafruit_DHT.DHT11

TIME_CONST = 4 # seconds the pump will go for
UPDATE_CONST = 1 # minutes to update values automatically

class PlantBuddy():
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PUMP_PHYS_PIN, GPIO.OUT)
        GPIO.output(PUMP_PHYS_PIN, GPIO.LOW) # close the transistor
        GPIO.setup(TH_DATA_PHYS_PIN, GPIO.IN)
        self.__time = time.time()
        self.__canPump, self.__isPumping = False, False
        self.__waterLevel, self.__temp, self.__hum, self.__soilMoisture = None, None, None, None
        self.__criticalThreshold = -1070 # value obtained by 50 tests and getting the max of those tests
        self.__warningThreshold = -1110 # again, value obtained from trial and error given the physicality of the prototype
        self.__emailStatus = { "warning_sent": False, "critical_sent": False }
        self.__updateState()
    
    def keepTime(self, _, __):
        while True:
            self.__time = time.time()
    
    def getTimeConstant(self):
        return TIME_CONST
    
    def getCritical(self):
        return self.__criticalThreshold
    
    def getWarning(self):
        return self.__warningThreshold
    
    def getIsPumping(self):
        return self.__isPumping
    
    def __updateState(self):
        self.__hum, self.__temp = self.getHumTemp()
        self.requestWaterLevel()
        self.requestSoilMoisture()
    
    def updateStateLoop(self, _, __):
        while True:
            time.sleep(60 * UPDATE_CONST)
            self.__updateState()
    
    def getState(self):
        return (self.__soilMoisture, self.__temp, self.__hum, self.__waterLevel)
    
    def resetEmailStatus(self, _, __):
        while True:
            time.sleep(60 * 60 * 24) # resets email statuses every 24 hours
            for item in self.__emailStatus:
                self.__emailStatus[item] = False
    
    def getHumTemp(self):
        # checks the temperature and relative humidity
        hum, temp = Adafruit_DHT.read_retry(DHT_SENSOR, TH_DATA_PHYS_PIN)
        return (hum, temp)
    
    def getWaterLevel(self):
        return self.__waterLevel
    
    def setWaterLevel(self, newWaterLevel):
        self.__waterLevel = newWaterLevel
        
    def setSoilMoisture(self, newSoilMoisture):
        self.__soilMoisture = newSoilMoisture
    
    def requestWaterLevel(self):
        # create an event that requests for the water level
        process = subprocess.Popen(["particle", "publish", "req_water_level"])
        return
    
    def requestSoilMoisture(self):
        # create event that requests soil moisture
        process = subprocess.Popen(["particle", "publish", "req_soil_moisture"])
        return
    
    def canPump(self):
        # checks if pumping water is permitted. updates __canPump
        # if water level is below critical threshold, relative to how sensor reads in
        if self.__waterLevel is not None and self.__waterLevel < self.__criticalThreshold:
            return True
        return False
    
    def pump(self, _, __):
        if self.canPump():
            t_end = self.__time + 5
            while self.__time < t_end:
                self.__isPumping = True
                # GPIO.output(PUMP_PHYS_PIN, GPIO.HIGH) # if the logic circuit were built
            self.__isPumping = False
            # GPIO.output(PUMP_PHYS_PIN, GPIO.LOW) # if the logic circuit were built
            self.__updateState() # vital, to get water level after pumping.
            print("Pump activation successful.")
            self.requestWaterLevel()
        else:
            print("Water level not yet captured or at critical level.")
    
    def sendReport(self, email):
        if email is not None:
            data = {
                "email": email,
                "soil_moisture": self.__soilMoisture,
                "temperature": self.__temp
            }
            data = json.dumps(data)
            process = subprocess.Popen(["particle", "publish", "email_report", data])
    
    def sendWarning(self, email):
        if self.__emailStatus["warning_sent"] == False and email is not None:
            data = {
                "email": email
            }
            data = json.dumps(data)
            process = subprocess.Popen(["particle", "publish", "warning_email", data])
            self.__emailStatus["warning_sent"] = True
        
    def sendCriticalWarning(self, email):
        if self.__emailStatus["critical_sent"] == False and email is not None:
            data = {
                "email": email
            }
            data = json.dumps(data)
            process = subprocess.Popen(["particle", "publish", "critical_email", data])
            self.__emailStatus["critical_sent"] = True
