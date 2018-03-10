#!/usr/bin/env python3

from bottle import route, run, template, view
import bottle
import datetime
import sys

bottle.TEMPLATES.clear()

# TODO: Fire off another async process from docker container that launches
# a web request every 5 minutes to have it refresh the status when
# the heat is on -- checks to turn it off, and in the other direction,
# checks to turn it on if its too cold.


######################################################
# Globals
######################################################

heat_target = 0
heat_mode = 'Off'



def get_conditions():
    """
    Returns the (temperature, humidity) as a tuple.
    """
    return (42,50)

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

    The returned dict is used in the 'result' template.
    """
    global heat_mode, heat_target

    (temp, humid) = get_conditions()
    return_value = {'mode':heat_mode, 'target':heat_target,
                    'temp':temp, 'humid':humid}
    if status == None:
        print('Status request')
        return return_value
    if status == 'Off':
        print('Turning off heater')
        heat_mode = 'Off'
        return_value['mode'] = heat_mode
        return return_value
    # Must be request to set target to certain temperature and turn on
    # the heat
    print('Turning on the heater')
    heat_mode = 'On'
    heat_target = status
    return_value['target'] = heat_target
    return_value['mode'] = heat_mode
    print('\t*** Return_Value = {}'.format(repr(return_value)))
    return return_value

# Return the current fan/heat status and the temperature/humid
@route('/')
@route('/status')
@view('result')
def index():
    my_dict = set_status(None)
    return my_dict

@route('/off')
@view('result')
def turn_system_off():
    my_dict = set_status('Off')
    return my_dict

@route('/on/<temp>')
@view('result')
def turn_heat_on_target(temp='72'):
    try:
        num_temp = int(temp)
    except:
        return template('error', error='Not a number, request must be "/on/<num>"')

    my_dict = set_status(num_temp)
    return my_dict

@route('/on')
@view('result')
def turn_heat_on():
    my_dict = set_status(heat_target)
    return my_dict



################################################
# Main Program
################################################

default_port = 80

def main(port_no):
    bottle.debug(True)
    bottle.run(host='0.0.0.0', port=port_no, debug=True)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        try:
            default_port = sys.argv[1]
        except:
            print('Usage: {} [port_num]'.format(sys.argv[0]), file=sys.stderr)
            sys.exit(2)
    bottle.debug(True)
    main(default_port)
