import RPi.GPIO as GPIO
from threading import Timer
import time
import atexit
from collections import OrderedDict

# IN  | OUT | Color
# 15  | 22  | Blue 
# 16  | 23  | Green
# 18  | 24  | Red

class Counter:
  pin_rotating = 16
  pin_pulse    = 18

  bounce_time = 50 #ms

  pout_rotating = 23
  pout_pulse    = 24

  rotations = 0

  def __init__(self):
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(self.pin_rotating, GPIO.IN)
    GPIO.setup(self.pin_pulse,    GPIO.IN)

    GPIO.setup(self.pout_rotating, GPIO.OUT)
    GPIO.setup(self.pout_pulse,    GPIO.OUT)

    GPIO.add_event_detect(self.pin_rotating, GPIO.BOTH,    callback = self.Rotation)
    GPIO.add_event_detect(self.pin_pulse,    GPIO.FALLING, callback = self.NumberCounter)

    self.StartCounting()

  def Rotation(self, channel):
    self.rotating = not GPIO.input(channel)
    GPIO.output(self.pout_rotating, self.rotating)

    if self.rotating:
      # print "\nStarted rotation"
      self.triggers[time.time()] = "Rotating START"
    else:
      self.triggers[time.time()] = "Rotating FINISH"

      r = self.rotations
      number = r / 2 + r % 2
      print "\nFinished rotation: %d" % self.rotations 
      print "Number: %d" % (number)

      Timer(0.5, self.Timing).start()

    self.rotations = 0
   
    
  def NumberCounter(self, channel):
    self.triggers[time.time()] = "Pulse"
    if self.rotating:
      self.rotations += 1
      print('.'),
    else:
      print('x'),


  def StartCounting(self):
    self.start_time = time.time()
    self.triggers = OrderedDict()

  def Timing(self):
    'Print timing of triggers captured'
 
    print "\n---\n"
    prev = 0

    for tt, trigger in self.triggers.iteritems():
      t = int(round( (tt - self.start_time) * 1000 ))
      print "%16s | +%6dms | %10dms " % (trigger, t-prev, t) 
      prev = t
      time.sleep(0.01) # For some strange reason sometimes flushing doesn't work correctly :/ adding this delay to help it print properly.

    self.StartCounting()

  def cleanup(self):
    GPIO.cleanup()    


c = Counter()

def cleanup():
  print "Cleaning up"
  GPIO.cleanup()    

atexit.register(cleanup)

while True:
  time.sleep(1)
