#!/usr/bin/env python
import sys
import argparse
import datetime
import subprocess
import shutil
import os

def increase_zone_serial(zone):
    "Increase the zone serial using the ldns-read-zone utility"
    exec_string = "ldns-read-zone -S YYYYMMDDxx {zone} > {zone}.tmp".format(zone=zone)
    subprocess.call(exec_string,shell=True)
    shutil.move(zone+".tmp",zone)

def find_keys(zone):
    """Find all the private keys in the same directory as the zonefile."""
    zonedir = os.path.dirname(zone)
    zonename = os.path.splitext(os.path.basename(zone))[0]
    keys = [f for f in os.listdir(zonedir) if zonename in f and ".private" in f]
    keys = [os.path.splitext(key)[0] for key in keys ]
    keys = " ".join([os.path.join(zonedir,key) for key in keys])
    return keys

def sign_zone(zone,keys):
    "Sign the zone using the provided keys with a fixed expiry date of one month and 2 days"
    # Set expiry date to one month plus 2 days from now
    today = datetime.date.today()
    expire = today.replace(month=today.month+1, day=today.day+2)
    expire = expire.strftime("%Y%m%d")
    exec_string = "ldns-signzone -e {expire} {zone} {keys}".format(expire=expire,zone=zone,keys=keys)
    subprocess.call(exec_string,shell=True)

def check_zone(zone):
    exec_string = "ldns-read-zone {zone} > /dev/null".format(zone=zone)
    retcode = subprocess.call(exec_string,shell=True)
    if not retcode:
        sys.exit("There is an error in {zone}".format(zone=zone))
        
def main(args):
    parser = argparse.ArgumentParser(description= """
    This script uses the ldns-utilities to sign a zone. It is meant to be used in crontab
    so that periodically zones are resigned.
    
    The original zone file will be overwritten so that the serial is increased. 
    This also means you lose all formatting. Be sure to back up your zonefile if you value that kind of thing.
    """)
    parser.add_argument('zone', metavar='zones', type=str, nargs='+', default = "",
                       help='a zonefile to be signed')
    args = parser.parse_args(args)
    for z in args.zone:
        check_zone(z)
        increase_zone_serial(z)
        keys = find_keys(z)
        sign_zone(z,keys)
    # Finally ask NSD to reload the zones
    subprocess.call("nsd-control reload",shell=True)
    
if __name__ == '__main__':
    main(sys.argv[1:])