#!/usr/bin/env python
"""
    Asari 2019 Software
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


from Processes import CamPoller
from Processes import BMP280Poller
import threading
import time
import logging

logging.basicConfig(filename='/home/pi/Ansari2019/example.log',format='%(asctime)s %(levelname)s %(message)s',level=logging.DEBUG)
logging.info("Software on")

if __name__ == '__main__':
  global cam
  global bmp280
  cam = CamPoller()
  bmp280 = BMP280Poller()
  try:
    cam.start()
    bmp280.start()
    while True:
      time.sleep(1)
  except:
    print ("Exception main")
    logging.info("Shutting down")
    cam.running = False
    cam.join()
    bmp280.running = False
    bmp280.join()
    logging.info("Bye")
