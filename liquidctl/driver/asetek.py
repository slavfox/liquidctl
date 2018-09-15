"""Experimental generic USB driver for fifth generation Asetek coolers.

Targets EVGA CLCs, the Corsair Hydro series (non Pro Asetek models), and second
generation Krakens from NZXT.

Copyright (C) 2018  Jonas Malaco
Copyright (C) 2018  each contribution's author

Incorporates work from OpenCorsairLink, OpenHWControl and leviathan, under the
terms of the GNU General Public License.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import itertools
import sys

import usb.core
import usb.util

import liquidctl.util

SUPPORTED_DEVICES = [   # (vendor, product, description)
    (0x1b1c, 0x0c02, 'Corsair Hydro H80i GT'),
    (0x1b1c, 0x0c03, 'Corsair Hydro H100i GTX'),
    (0x1b1c, 0x0c07, 'Corsair Hydro H110i GTX'),
    (0x1b1c, 0x0c08, 'Corsair Hydro H80i v2'),
    (0x1b1c, 0x0c09, 'Corsair Hydro H100i v2'),
    (0x1b1c, 0x0c0a, 'Corsair Hydro H115i'),
    (0x2433, 0xb200, 'EVGA CLC 120/240/280 or Kraken X31/X41/X51'),
]
READ_ENDPOINT = 0x82
READ_LENGTH = 32
READ_TIMEOUT = 2000
WRITE_ENDPOINT = 0x2
WRITE_LENGTH = 32
WRITE_TIMEOUT = 2000


class AsetekDriver:
    """Generic USB driver for fifth generation Asetek coolers."""

    def __init__(self, device, description):
        self.device = device
        self.description = description
        self._should_reattach_kernel_driver = False

    @classmethod
    def find_supported_devices(cls):
        devs = []
        for vid, pid, desc in SUPPORTED_DEVICES:
            usbdevs = usb.core.find(idVendor=vid, idProduct=pid, find_all=True)
            devs = devs + [cls(i, desc) for i in usbdevs]
        return devs

    def initialize(self):
        if sys.platform.startswith('linux') and self.device.is_kernel_driver_active(0):
            liquidctl.util.debug('detaching currently active kernel driver')
            self.device.detach_kernel_driver(0)
            self._should_reattach_kernel_driver = True
        self.device.set_configuration()
        # self.device.ctrl_transfer(0x40, 0x0, 0xffff, 0x0)
        self.device.ctrl_transfer(0x40, 0x2, 0x0002, 0x0)

    def finalize(self):
        # finalize_timeout = 200
        # self.device.ctrl_transfer(0x40, 0x2, 0x0004, 0x0, timeout=finalize_timeout)
        usb.util.dispose_resources(self.device)
        if self._should_reattach_kernel_driver:
            liquidctl.util.debug('reattaching previously active kernel driver')
            self.device.attach_kernel_driver(0)

    def set_color(self, channel, mode, colors, speed):
        raise NotImplemented("TODO")

    def set_speed_profile(self, channel, profile):
        raise NotImplemented("TODO")

    def set_fixed_speed(self, channel, speed):
        raise NotImplemented("TODO")

    def get_status(self):
        # self._write([0x20])
        msg = self.device.read(READ_ENDPOINT, READ_LENGTH, READ_TIMEOUT)
        liquidctl.util.debug('read {}'.format(' '.join(format(i, '02x') for i in msg)))
        firmware = '{}.{}.{}.{}'.format(msg[0x17], msg[0x18], msg[0x19], msg[0x1a])
        return [
            ('Liquid temperature', msg[10] + msg[14]/10, '°C'),
            ('Fan speed', msg[0] << 8 | msg[1], 'rpm'),
            ('Pump speed', msg[8] << 8 | msg[9], 'rpm'),
            ('Firmware version', firmware, '')
        ]

    def _write(self, data):
        liquidctl.util.debug('write {}'.format(' '.join(format(i, '02x') for i in data)))
        padding = [0x0]*(WRITE_LENGTH - len(data))
        if liquidctl.util.dryrun:
            return
        self.device.write(WRITE_ENDPOINT, data + padding, WRITE_TIMEOUT)

