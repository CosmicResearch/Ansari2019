"""
    Ansari Software
    Copyright (C) 2016 Associacio Cosmic Research

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import RPi.GPIO as GPIO
import threading
import os
import os.path
import ConfigParser
import logging

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
from bmp280 import BMP280


class BMP280Poller(threading.Thread):
  def __init__(self):
    logging.debug("initializating BMP")
    threading.Thread.__init__(self)
    config = ConfigParser.ConfigParser()
    config.read("/home/pi/Ansari2019/config.ini")
    self.led = int(config.get("LED", "ledCam"))
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(self.led,GPIO.OUT)
    self.rateTime = float(config.get("BMP280", "rate_time"))
    self.measures = int(config.get("BMP280", "measures"))

    self.kalman = Kalman()
    self.speaker = Speaker()

    bus = SMBus(1)
    global bmp280
    bmp280 = BMP280(i2c_dev=bus)
    self.current_value = None
    self.running = True

  def run(self):
    logging.debug("bmp280 thread running")
    global bmp280

    #Compute baseline altitude
    baseline_values = []
    baseline_size = 50
    print("Collecting baseline values for {:d} seconds. Do not move the sensor!\n".format(baseline_size/10))
    for i in range(baseline_size):
      pressure = bmp280.get_pressure()
      baseline_values.append(pressure)
      time.sleep(.1)
    baselineAltitude = sum(baseline_values[:-25]) / len(baseline_values[:-25])
    print('Baseline altitude: {:05.2f} metres'.format(baselineAltitude))

    # Let's do some summy readings to initialize the Kalman filter
    for i in range(50):
      self.kalman.calcAltitude(bmp280.get_altitude(qnh=baselineAltitude))

    #Initialize some variables
    currMeasures = self.measures
    apogeeAltitude = 0
    lastAltitude = 0
    liftoffAltitude = 1
    apogeeReached = False

    #Beep, I'm ready
    #self.speaker.beginBeep()

    while self.running:
      #Read Current Altitude
      currAltitude = self.kalman.calcAltitude(bmp280.get_altitude(qnh=baselineAltitude))
      #print('Relative altitude: {:05.2f} metres'.format(currAltitude))

      #Detect Apogee
      if currAltitude > liftoffAltitude:
        if currAltitude < lastAltitude:
          currMeasures = currMeasures -1
          print('Measures: {:05.2f} '.format(currMeasures))
          if currMeasures == 0:
            apogeeAltitude = currAltitude
            apogeeReached = True
            print('Apogee altitude: {:05.2f} metres'.format(apogeeAltitude))
        else:
          lastAltitude = currAltitude
          currMeasures =  self.measures

      if apogeeReached == True and currAltitude < 50:
        #Begin beep
        print("miomoimiomiomoimo")
        self.speaker.altitudeBeep(apogeeAltitude)
      time.sleep(self.rateTime)

    GPIO.cleanup()

class Speaker():
  def __init__(self):
    config = ConfigParser.ConfigParser()
    config.read("/home/pi/Ansari2019/config.ini")
    self.pinSpeaker = int(config.get("BUZZER", "pinSpeaker"))
    self.freq = int(config.get("BUZZER", "frequency"))
    self.duttyc = float(config.get("BUZZER", "dutty_cycle"))
    GPIO.setup(self.pinSpeaker,GPIO.OUT)
    self.pwm = GPIO.PWM(self.pinSpeaker, self.freq)

  def beginBeep(self):
    for i in range(5):
      self.pwm.start(self.duttyc)
      time.sleep(0.5)
      self.pwm.stop()
      time.sleep(0.5)

  def longBeep(self):
    self.pwm.start(self.duttyc)
    time.sleep(1.5)
    self.pwm.stop()

  def shortBeep(self):
    self.pwm.start(self.duttyc)
    time.sleep(0.3)
    self.pwm.stop()

  def altitudeBeep(self,altitude):
    if altitude > 99:
      nLongBeep = (int) (altitude / 100)
      nShortBeep = (int) (altitude - (nLongBeep * 100)/10)
    else:
      nLongBeep = 0
      nShortBeep = (int) (altitude/10)

    if nLongBeep > 0:
      for i in range(nLongBeep):
        self.longBeep()

    if nShortBeep > 0:
      for i in range(nShortBeep):
        self.shortBeep()

    time.sleep(5)


class Kalman():
  def __init__(self):
    config = ConfigParser.ConfigParser()
    config.read("/home/pi/Ansari2019/config.ini")

    self.q = float(config.get("KALMAN", "q"))
    self.r = float(config.get("KALMAN", "q"))

    self.x = 0
    self.p = 0
    self.x_temp = 0
    self.p_temp = 0
    self.x_last = 0
    self.p_last = 0

  def calcAltitude(self, altitude):
    #Predict kalman x_temp and p_temp
    self.x_temp = self.x_last
    self.p_temp = self.p_last + self.r

    #Update kalman values
    self.k = self.p_temp/(self.p_temp+self.q)
    self.x = self.x_temp + self.k*(altitude-self.x_temp)
    self.p = self.p_temp*(1-self.k)

    # Save this statefor next time
    self.x_last = self.x
    self.p_last = self.p

    # Assign current kalman filtered altitude to working variables
    return self.x


