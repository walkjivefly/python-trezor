# This file is part of the TREZOR project.
#
# Copyright (C) 2012-2016 Marek Palatinus <slush@satoshilabs.com>
# Copyright (C) 2012-2016 Pavol Rusnak <stick@satoshilabs.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import unittest
import hashlib

from trezorlib.client import TrezorClient, TrezorClientDebugLink
from trezorlib import tx_api


tx_api.cache_dir = '../txcache'


try:
    from trezorlib.transport_hid import HidTransport
    HID_ENABLED = True
except Exception as e:
    print('HID transport disabled:', e.message, e.args)
    HID_ENABLED = False

try:
    from trezorlib.transport_pipe import PipeTransport
    PIPE_ENABLED = True
except Exception as e:
    print('PIPE transport disabled:', e.message, e.args)
    PIPE_ENABLED = False

try:
    from trezorlib.transport_udp import UdpTransport
    UDP_ENABLED = True
except Exception as e:
    print('UDP transport disabled:', e.message, e.args)
    UDP_ENABLED = False


def pipe_exists(path):
    import os
    import stat
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except:
        return False


if HID_ENABLED and HidTransport.enumerate():

    devices = HidTransport.enumerate()
    print('Using TREZOR')
    TRANSPORT = HidTransport
    TRANSPORT_ARGS = (devices[0],)
    TRANSPORT_KWARGS = {}
    DEBUG_TRANSPORT = HidTransport
    DEBUG_TRANSPORT_ARGS = (devices[0].find_debug(),)
    DEBUG_TRANSPORT_KWARGS = {}

elif PIPE_ENABLED and pipe_exists('/tmp/pipe.trezor.to'):

    print('Using Emulator (v1=pipe)')
    TRANSPORT = PipeTransport
    TRANSPORT_ARGS = ('/tmp/pipe.trezor', False)
    TRANSPORT_KWARGS = {}
    DEBUG_TRANSPORT = PipeTransport
    DEBUG_TRANSPORT_ARGS = ('/tmp/pipe.trezor_debug', False)
    DEBUG_TRANSPORT_KWARGS = {}

elif UDP_ENABLED:

    print('Using Emulator (v2=udp)')
    TRANSPORT = UdpTransport
    TRANSPORT_ARGS = ('', )
    TRANSPORT_KWARGS = {}
    DEBUG_TRANSPORT = UdpTransport
    DEBUG_TRANSPORT_ARGS = ('', )
    DEBUG_TRANSPORT_KWARGS = {}


class TrezorTest(unittest.TestCase):

    def setUp(self):
        transport = TRANSPORT(*TRANSPORT_ARGS, **TRANSPORT_KWARGS)
        debug_transport = DEBUG_TRANSPORT(*DEBUG_TRANSPORT_ARGS, **DEBUG_TRANSPORT_KWARGS)
        self.client = TrezorClientDebugLink(transport)
        self.client.set_debuglink(debug_transport)
        self.client.set_tx_api(tx_api.TxApiBitcoin)
        # self.client.set_buttonwait(3)

        #                     1      2     3    4      5      6      7     8      9    10    11    12
        self.mnemonic12 = 'alcohol woman abuse must during monitor noble actual mixed trade anger aisle'
        self.mnemonic18 = 'owner little vague addict embark decide pink prosper true fork panda embody mixture exchange choose canoe electric jewel'
        self.mnemonic24 = 'dignity pass list indicate nasty swamp pool script soccer toe leaf photo multiply desk host tomato cradle drill spread actor shine dismiss champion exotic'
        self.mnemonic_all = ' '.join(['all'] * 12)

        self.pin4 = '1234'
        self.pin6 = '789456'
        self.pin8 = '45678978'

        self.client.wipe_device()

        print("Setup finished")
        print("--------------")

    def setup_mnemonic_allallall(self):
        self.client.load_device_by_mnemonic(mnemonic=self.mnemonic_all, pin='', passphrase_protection=False, label='test', language='english')

    def setup_mnemonic_nopin_nopassphrase(self):
        self.client.load_device_by_mnemonic(mnemonic=self.mnemonic12, pin='', passphrase_protection=False, label='test', language='english')

    def setup_mnemonic_pin_nopassphrase(self):
        self.client.load_device_by_mnemonic(mnemonic=self.mnemonic12, pin=self.pin4, passphrase_protection=False, label='test', language='english')

    def setup_mnemonic_pin_passphrase(self):
        self.client.load_device_by_mnemonic(mnemonic=self.mnemonic12, pin=self.pin4, passphrase_protection=True, label='test', language='english')

    def tearDown(self):
        self.client.close()


def generate_entropy(strength, internal_entropy, external_entropy):
    '''
    strength - length of produced seed. One of 128, 192, 256
    random - binary stream of random data from external HRNG
    '''
    if strength not in (128, 192, 256):
        raise Exception("Invalid strength")

    if not internal_entropy:
        raise Exception("Internal entropy is not provided")

    if len(internal_entropy) < 32:
        raise Exception("Internal entropy too short")

    if not external_entropy:
        raise Exception("External entropy is not provided")

    if len(external_entropy) < 32:
        raise Exception("External entropy too short")

    entropy = hashlib.sha256(internal_entropy + external_entropy).digest()
    entropy_stripped = entropy[:strength // 8]

    if len(entropy_stripped) * 8 != strength:
        raise Exception("Entropy length mismatch")

    return entropy_stripped
