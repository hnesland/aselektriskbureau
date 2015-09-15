import RPi.GPIO as GPIO

class Tester:
  def __init__(self):
    self.board_mode()
    self.setup()
    self.light()

  def board_mode(self):
    GPIO.setmode(GPIO.BOARD)
    self.in_to_out = {15: 22, 16: 23, 18: 24}

  def bcm_mode(self):
    GPIO.setmode(GPIO.BCM)
    self.in_to_out = {22: 25, 24: 11, 24: 8}

  def setup(self):
    for p_in, p_out in self.in_to_out.iteritems():
      GPIO.setup(p_in, GPIO.IN)
      GPIO.setup(p_out, GPIO.OUT)

  def light(self):
    for p_in, p_out in self.in_to_out.iteritems():
      GPIO.output(p_out, not GPIO.input(p_in))

  def test(self):
    while True:
      self.light()

  def cleanup(self):
    GPIO.cleanup()    

    
