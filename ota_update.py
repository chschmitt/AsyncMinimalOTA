import requests
import argparse
import pathlib
import hashlib
import sys
import os

from zeroconf import ServiceBrowser, Zeroconf
from concurrent.futures import Future

from requests.auth import HTTPDigestAuth

class ESPFinder:
    def __init__(self, espid):
        self.espid = espid
        self.expected_suffix = f'-{espid}'
        self.future = Future()
        self.wait = self.future.result

    def remove_service(self, zeroconf, type, name):
        pass

    def decode(self, value):
        return value.decode(errors='ignore', encoding='utf-8')

    def add_service(self, zeroconf, type, name):
        if self.future.done():
            return

        info = zeroconf.get_service_info(type, name)
        addresses = info.parsed_addresses()
        if not addresses:
            return
        host = addresses[0]

        def found():
            self.future.set_result(host)


        properties = { self.decode(k): self.decode(v) for  k, v in info.properties.items() }
        if properties.get('espid') == self.espid:
            return found()

        name2 = info.get_name()
        if name2 and name2.endswith(self.expected_suffix):
            return found()

        name3 = properties.get('name') 
        if name3 and name3.endswith(self.expected_suffix):
            return found()


def find_esp(espid, timeout=10):
    zeroconf = Zeroconf()
    listener = ESPFinder(espid)
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    return listener.wait(timeout)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-f', '--firmware')
    p.add_argument('--espid')
    p.add_argument('--host')
    p.add_argument('--user', default=os.environ.get('OTA_USER', 'ota'))
    p.add_argument('--password', default=os.environ.get('OTA_PASSWORD', ''))
    return p.parse_args()

def main():
    args = parse_args()
    if not args.host:
        if not args.espid:
            print('host or espid must be specified')
            return 1
        
        args.host = find_esp(args.espid)
        print(f'address of {args.espid} is {args.host}')

    # return
    auth = HTTPDigestAuth(args.user, args.password)
    url = f'http://{args.host}/update'
    r = requests.get(f'{url}/identity', auth=auth)
    r.raise_for_status()
    device_id = r.json()['id']

    if args.espid and args.espid != device_id:
        print(f'ESP ID mismatch: wanted {args.espid}, got {device_id}')
        return 1
    print(f'ESP ID verified: {device_id}')

    if not args.firmware:
        print('no firmware file specified')
        return 2

    fwpath = pathlib.Path(args.firmware)
    fwdata = fwpath.read_bytes()
    fwhash = hashlib.md5(fwdata).hexdigest()
    print(f'firmware hash is md5={fwhash}')

    r = requests.post(url, auth=auth, files={
        "MD5": (None, fwhash),
        "firmware": ("firmware", fwdata, "application/octet-stream"),
    })
    print(r)
    print(r.text)

if __name__ == '__main__':
    ret = main()
    if ret:
        sys.exit(ret)