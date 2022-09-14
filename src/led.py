import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library

GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering

def initialize_led_pin(pin):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def set_led_output(status):
    if status:
        GPIO.output(3, GPIO.HIGH)
    else:
        GPIO.output(3, GPIO.LOW)
