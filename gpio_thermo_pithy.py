import time
import Adafruit_DHT
from datetime import datetime
import RPi.GPIO as GPIO

# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
sensor = Adafruit_DHT.AM2302


PIN_HEAT = 17   # RPI PIN 11
PIN_FAN = 22    # RPI PIN 15
OUTPINS = [PIN_HEAT, PIN_FAN]

PIN_SENSOR = 27   # GPIO27, or PIN 13

SENSOR_RETRIES = 5          # Number of reads from DHT before
                             # moving to the cache

class Thermostat:
    """
    Class that instantiates a production version of the GPIO heater and
    fan pins for the Thermostat in Pt Reyes Station.

    Also, instantiates the current temperature functions using a DHT sensor.

    HEAT is on GPIO 17
    FAN is on GPIO 22
    DHT Sensor is on GPIO 27

    In all cases, both of HEAT/FAN pins MUST have the same state, either ON
    or OFF.  I'm not sure what happens, for instance, if the HEAT is ON
    but the FAN is OFF.  Does it cause a fire?

    [2018-03-09 FRI 21:59]
    """



    def __init__(self, mode=False):
        self.gpio_state = mode  # Simulated heat/fan GPIO status
        self.temp = 60.0          # Simulated current temperature
        self.humid = 50.0         # Simulated current humidity

        self.cache_time = 0
        self.cache_temp = -10.0
        self.cache_humid = 0

        # Default GPIO modes for HEATER/FAN
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in OUTPINS:
            GPIO.setup(pin, GPIO.OUT)
            # Set initial state to off.  GPIO.HIGH is OFF.  LOW is ON
            GPIO.output(pin, GPIO.HIGH)

        # Set up thermostat pin
        GPIO.setup(PIN_SENSOR, GPIO.IN)



    def gpio_status(self, mode=None):
        """
        This function is where we actually switch on the GPIO pins for the
        Heater and the Fan based on what MODE is passed in.

        Overloaded MODE where:
            - False, turns off heat/fan
            - True, turns on heat/fan
            - None, just returns status of the Thermo system
        """
        if mode == True:
            print('gtd: status(True), was {}'.format(repr(self.gpio_state)))
            GPIO.output(PIN_HEAT, 0)
            GPIO.output(PIN_FAN, 0)
            self.gpio_state = True
        elif mode == False:
            print('gtd: status(False), was {}'.format(repr(self.gpio_state)))
            GPIO.output(PIN_HEAT, 1)
            GPIO.output(PIN_FAN, 1)
            self.gpio_state = False

        # In any case, and especially if the incoming parameter MODE is None,
        # the return value of GPIO_STATUS is the state of the GPIO pins.

        return self.gpio_state

    def get_conditions(self):
        """
        Function to return a tuple of the (temp, humid) for the
        temp sensor.
        """
        for i in range(SENSOR_RETRIES):
            humidity, temperature = Adafruit_DHT.read(sensor, PIN_SENSOR)
            print('Success on sensor, reading {}'.format(
                    repr((temperature, humidity))))
            if humidity and temperature:
                break
        if i < SENSOR_RETRIES:
            # Convert to Farenheiht
            tempf = temperature * 9.0 / 5.0 + 32.0
            temperature = tempf

            # Success!
            self.cache_temp = temperature
            self.cache_humid = humidity
            self.cache_time = datetime.now()
            print('Returning real temperature {} at {}'.format(
                    repr((temperature, humidity)),
                    repr(self.cache_time)))
            return (temperature, humidity)

        # Must be failure at this point, use the cache
        print('gtp: Too many failures on sensor read ', SENSOR_RETRIES)
        print('Using stale cache values of {} from {}'.format(
                repr((self.cache_temp, self.cache_humid)),
                repr(self.cache_time)))
        return (self.cache_temp, self.cache_humid)

    def sim_set_conditions(self, temp=None, humid=None):
        """
        Simulator function (called by web services stubs) to set the
        simulated conditions from the temperature sensor.

        For this production class, if this function is called, then
        we will forever used forced cached values without even
        trying to read the sensor.
        """

        MAX_RETRIES = 0                     # Force always using cache

        if temp:
            self.cache_temp = temp
        if humid:
            self.cache_humid= humid

        self.cache_time = datetime.now()

        print('gtd: sim_set_conditions{} on {}'.format(
            repr((temp, humid)), repr(self.cache_time)))
