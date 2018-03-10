
class Thermostat:
    """
    Class that instantiates a debug version of the GPIO heater and
    fan pins for the Thermostat in Pt Reyes Station.

    [2018-03-09 FRI 21:59]
    """

    def __init__(self, mode=False):
        self.gpio_state = mode  # Simulated heat/fan GPIO status
        self.temp = 60.0          # Simulated current temperature
        self.humid = 50.0         # Simulated current humidity


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
            # TODO: Turn on the GPIO for Heat and Fan
            self.gpio_state = True
        elif mode == False:
            print('gtd: status(False), was {}'.format(repr(self.gpio_state)))
            # TODO: Turn off the GPIO for Heat and Fan
            self.gpio_state = False
            
        # In any case, and especially if the incoming parameter MODE is None,
        # the return value of GPIO_STATUS is the state of the GPIO pins.

        return self.gpio_state

    def get_conditions(self):
        """
        Function to return a tuple of the (temp, humid) for the simulated
        temp sensor.
        """
        return (self.temp, self.humid)

    def sim_set_conditions(self, temp=None, humid=None):
        """
        Simulator function (called by web services stubs) to set the
        simulated conditions from the temperature sensor.  This won't
        be present in the production Thermostat class because
        we won't need to do that.
        """
        if temp:
            self.temp = temp
        if humid:
            self.humid = humid
        print('gtd: sim_set_conditions{}'.format(repr((temp, humid))))
