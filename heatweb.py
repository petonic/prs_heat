#!/usr/bin/env python3

from bottle import route, run, template, view
import bottle
from datetime import datetime
import sys

import time

from gpio_thermo_pithy import Thermostat



thermo = Thermostat()

bottle.TEMPLATES.clear()

# TODO: Fire off another async process from docker container that launches
# a web request every 5 minutes to have it refresh the status when
# the heat is on -- checks to turn it off, and in the other direction,
# checks to turn it on if its too cold.


######################################################
# Globals
######################################################

# Tolerances for switching on/off the heat
hyst_low = 1.5
hyst_high = 1.0

# Default values
default_port = 80
default_interval = 5

# Initial values for globals
heat_target = 0
heat_mode = False

LOGFILE = '/var/log/heatweb.log'


def get_status():
    """
    Returns, as a tuple, the (heat, fan) operating status.
    """
    return ('off', 'off')


def set_status(status):
    """
    Sets the fan/heat status to 'status' (None, 'Off', <int>):
      - None: Just gets temp/humid values for rendering status
      - 'Off': Does above, but also shuts heat/fan off
      - <int>: Turns the heat on and sets internal heat limit to <int>

    Function returns the system status (after any actions) as a dict:
      mode: 'On', 'Off', <int>
      temp: <float>Temperature from sensor
      humid: <float>Temperature from sensor
      target: <int>Target temperature

    The returned dict is used in the 'status' template.
    """
    global heat_mode, heat_target

    (temp, humid) = thermo.get_conditions()
    return_value = {'mode':heat_mode, 'target':heat_target,
                    'temp':temp, 'humid':humid,
                    'gpio_state':thermo.gpio_status()}
    if status == None:
        print('Status request')
        return return_value
    if status == 'Off':
        print('Turning off heater')
        thermo.gpio_status(False)
        heat_mode = False
        return_value['mode'] = heat_mode
        return return_value
    # STATUS == True.  Must be a request to set target to certain
    # temperature and turn on the heat
    print('Turning on the heater')
    heat_mode = True
    thermo.gpio_status(True)
    return_value['gpio_state'] = True
    heat_target = status
    return_value['target'] = heat_target
    return_value['mode'] = heat_mode
    print('\t*** Return_Value = {}'.format(repr(return_value)))
    return return_value

# Return the current fan/heat status and the temperature/humid
@route('/')
@route('/status')
@view('status')
def index():
    my_dict = set_status(None)
    return my_dict

@route('/off')
@view('status')
def turn_system_off():
    my_dict = set_status('Off')
    return my_dict

@route('/on/<target:int>')
@route('/on')
@view('status')
def turn_heat_on_target(target=None):
    if target:
        try:
            num_target = int(target)
        except:
            return template('error', error='Not a number, request must be "/on/<num>"')
    else:
        # if no target supplied, use existing target
        num_target = heat_target

    my_dict = set_status(num_target)
    return my_dict


@route('/rest/status')
def rest_status():
    """
    REST call to return a JSON dict with the current status to the
    requestor.
    """
    my_dict = set_status(None)
    return my_dict

def do_thermostat_things():
    """
    Gets called by other functions to do the business logic of
    setting the following:
        - if (heat_mode == False)
            if temp > heat_target + 1.0:
                turn off heat/fan
        - if (heat_mode == True)
            if temp < heat_target - 1.5:
                turn on heat/fan
    """

    global heat_mode, heat_target
    global hyst_low, hyst_high

    (temp, humid) = thermo.get_conditions()

    if heat_mode:
        # Check to see if we need to turn off the heat
        if temp > (heat_target + hyst_high):
            print('--- HEATING_MODE, upper limit reached, ensure it\'s off')
            if thermo.gpio_status():
                print('--- **** WAS NOT TURNED OFF, turning off')
            thermo.gpio_status(False)
        if temp < (heat_target - hyst_low):
            print('--- HEATING MODE, lower limit reached, ensure its on')
            if not(thermo.gpio_status()):
                print('--- **** WAS NOT TURNED ON, turning on')
            thermo.gpio_status(True)
    # else:
    #     # Heat is switched off, so make sure that the GPIO
    #     # actually reflects this
    #     if thermo.gpio_status():
    #         print('--- NON_HEAT mode, gpio heat is on tho, turning off')
    #         thermo.gpio_status(False)

@route('/refresh')
def rest_refresh():
    """
    Intended to be called periodically, say, once every 5 minutes or so,
    in order to call 'do_thermo_things()', which actually sets/unsets the GPIO
    for heating.  Written this way with this additional layer of rest_refresh()
    because I want other functions to also call do_thermostat_things() as well
    for when new parameters are set.add

    Also, logs the current status into a logfile in /var/log/webheat.log
    {"mode": false, "humid": 1.0, "gpio_state": false, "target": 0, "temp": 69.98000068664551}
    """
    do_thermostat_things()
    my_dict = set_status(None)
    now_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_dict = my_dict
    log_dict['mode'] = 'HEAT-ON' if my_dict['mode'] else 'heat-off'
    log_dict['gpio_state'] = '---GPIOS-ON---' if \
        my_dict['gpio_state'] else 'gpios-off'

    with open(LOGFILE, 'a') as logf:
        print('{},{},{},{:.2f},{:.2f},{}'.format(
                now_string, log_dict['mode'], log_dict['target'],
                log_dict['temp'], log_dict['humid'], log_dict['gpio_state']),
              file=logf)
    return my_dict

@route('/set/<temp:float>')
@route('/set/<temp:float>,<humid:float>')
@view('status')
def set_conditions(temp=None, humid=None):
    """
    This route is used to artificially set the simulated temperature
    sensor during debugging phases. This will not be used in a production
    run.
    """
    if temp == None:
        print('=== pretty stupid error, not setting temperature on'
              ' set_conditions()')
    thermo.sim_set_conditions(temp, humid)
    my_dict = set_status(None)
    # This will render a normal status frame in HTML
    return my_dict

from multiprocessing import Process

################################################
# Child process code to do refreshes
################################################
def poll_http(interval, port_no):
    """
    Called from a separate thread that executes every INTERVAL seconds.  All
    it does is wake up, uses requests to call the '0.0.0.0:<port>/refresh'
    URL so that the main thread can set the GPIO values.
    """
    import requests

    url_string = 'http://0.0.0.0:{}/refresh'.format(port_no)

    print('DBG: poll_http({}): got to thread @ {}'.format(
            interval, time.strftime("%I:%M:%S")))
    print('url_string = {}'.format(repr(url_string)))

    while True:
        time.sleep(interval)
        print('DBG: thread woke up @ {}'.format(time.strftime("%I:%M:%S")))
        r = requests.get(url_string)
        print('DBG: Requests.text = {}'.format(repr(r.text)))


################################################
# Main Program
################################################
def main(port_no=default_port, interval=default_interval):
    bottle.debug(True)

    # Start the other thread that wakes up every so often and hits
    # the '/refresh' page.  This allows the thermostat to check to make
    # sure that the heater/fan is on when it should be on, and off when it
    # should be off.
    Process(target=poll_http, args=[interval, port_no]).start()

    bottle.run(host='0.0.0.0', port=port_no, debug=True)


if __name__ == '__main__':
    interval = default_interval

    def usage():
        print('Usage: {} [port_num [interval_in_secs]]'.format(sys.argv[0]),
              file=sys.stderr)
        sys.exit(2)

    if len(sys.argv) >= 2:
        try:
            default_port = int(sys.argv[1])
        except:
            print('{}: port not supplied as INT: {}'.format(repr(
                    sys.argv[0], sys.argv[1])))
            usage()

    if len(sys.argv) == 3:
        try:
            interval = int(sys.argv[2])
        except:
            print('{}: interval not supplied as INT: {}'.format(repr(
                    sys.argv[0], sys.argv[2])))
            usage()


    bottle.debug(True)
    main(default_port, interval)
