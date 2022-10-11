import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library

GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO_PIN = 8
GPIO.setup(GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)


def set_led_output(status):
    if status:
        GPIO.output(GPIO_PIN, GPIO.HIGH)
    else:
        GPIO.output(GPIO_PIN, GPIO.LOW)


def cleanup():
    GPIO.cleanup()
