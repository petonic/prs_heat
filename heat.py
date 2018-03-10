#!/usr/bin/env python3

from bottle import route, run, template
import bottle
import datetime
import sys

# TODO: Fire off another async process from docker container that launches
# a web request every 5 minutes to have it refresh the status when
# the heat is on -- checks to turn it off, and in the other direction,
# checks to turn it on if its too cold.


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

def generate_html_page(system_status):
    """
    Uses the template to generate an HTML page that indicates the current
    system status, as well as whether we just turned ON or OFF the system.
    An empty value of 'operation' will mean to just show the system status
    without turning on or off the fans/heat.
    """
    try:
        (temp, humid) = get_conditions()
    except:
        return template('error', 'getting conditions')

    try:
        (stat_heat, stat_fan) = get_status()
    except:
        return template('error', 'getting environmental status')

    print('Going to call template on ({})'.format(repr((
            system_status, stat_heat, stat_fan,temp,humid))))

    return template('result', operation=system_status, stat_heat=stat_heat,
                    stat_fan=stat_fan, temp=temp, humid=humid)

# Return the current fan/heat status and the temperature/humid
@route('/')
@route('/status')
def index():
    print('Generating index')
    generate_html_page(None)

@route('off')
def turn_system_off():
    pass    # Pretend that we're turning the system off
    return generate_html_page('off')

@route('/on/<temp>')
def turn_heat_on(temp='72'):
    try:
        num_temp = int(temp)
    except:
        return template('error', error='Not a number, request must be "/on/<num>"')
    pass    # Pretend we're turning on the heat to num_temp degrees
    return generate_html_page(num_temp)


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
