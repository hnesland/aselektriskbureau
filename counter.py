import RPi.GPIO as GPIO
from threading import Timer
import time

# IN  | OUT | Color
# 15  | 22  |  
# 16  | 23  | Green
# 18  | 24  |

class Counter:
  pin_rotating = 16
  pin_pulse    = 18

  bounce_time = 50 #ms

  pout_rotating = 23
  pout_pulse    = 24

  def __init__(self):
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(self.pin_rotating, GPIO.IN)
    GPIO.setup(self.pin_pulse,    GPIO.IN)

    GPIO.setup(self.pout_rotating, GPIO.OUT)
    GPIO.setup(self.pout_pulse,    GPIO.OUT)

    GPIO.add_event_detect(self.pin_rotating, GPIO.BOTH,    callback = self.Rotation)
    GPIO.add_event_detect(self.pin_pulse,    GPIO.FALLING, callback = self.NumberCounter)


  def Rotation(self, channel):
    self.rotating = not GPIO.input(channel)
    GPIO.output(self.pout_rotating, self.rotating)

    if self.rotating:
      print "\nStarted rotation"
    else:
      print "\nFinished rotation: %d" % self.rotations

    self.rotations = 0
   
    
  def NumberCounter(self, channel):
    self.rotations += 1

    if self.rotating:
      print('.'),
    else:
      print('x'),

  def cleanup(self):
    GPIO.cleanup()    


c = Counter()


while True:
  time.sleep(1)
