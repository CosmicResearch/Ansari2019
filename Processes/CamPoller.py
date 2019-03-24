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

import picamera
import RPi.GPIO as GPIO
import threading
import os
import os.path
import ConfigParser
import logging

#camera = None
#led = 12
#duration = 30
#path = '/home/pi/Videos/'

class CamPoller(threading.Thread):
  def __init__(self):
    logging.debug("Initializating camera")
    threading.Thread.__init__(self)
    config = ConfigParser.ConfigParser()
    config.read("/home/pi/Ansari2019/config.ini")
    self.led = int(config.get("LED", "ledCam"))
    self.fps = int(config.get("CAMERA","fps"))
    self.resx = int(config.get("CAMERA","resolutionX"))
    self.resy = int(config.get("CAMERA","resolutionY"))
    self.duration = int(config.get("CAMERA","duration"))
    self.path = str(config.get("CAMERA","savedPath"))
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(self.led,GPIO.OUT)
    GPIO.output(self.led,GPIO.HIGH)
    global camera
    camera=picamera.PiCamera(resolution=(self.resx, self.resy),framerate=self.fps)
    self.current_value = None
    self.running = True

  def run(self):
    logging.debug("Camera  running")
    global camera
    if not os.path.exists(self.path):
      os.makedirs(self.path)
      logging.debug("New Video folder created at user folder")
    for i in range (0,9999):
      if not os.path.exists(self.path+'vid_%04d.h264' % i):
        break
      i = i + 1
    GPIO.output(self.led,GPIO.LOW)
    camera.start_recording(self.path+'vid_%04d.h264' % i)
    try:
      print (self.duration)
      camera.wait_recording(self.duration)
      print ("Video 1 recorded")
    except PiCameraError:
      GPIO.output(self.led,PIO.HIGH)
    while self.running:
      print ("running thread")
      i=i+1
      camera.split_recording(self.path+'vid_%04d.h264' % i)
      try:
        camera.wait_recording(self.duration)
      except PiCameraError:
        GPIO.output(self.led,GPIO.HIGH)
    camera.stop_recording()
