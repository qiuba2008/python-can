# -*- coding: utf-8 -*-

"""
Name:        serial_test
Purpose:     Testing the serial interface

Copyright:   2017 Boris Wenzlaff

This file is part of python-can <https://github.com/hardbyte/python-can/>.

python-can is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

python-can is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with python-can. If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
import can
from can.interfaces.serial.serial_can import SerialBus
from mock import patch


class SerialDummy:
    """
    Dummy to mock the serial communication
    """
    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1):
        return_value = bytearray()
        for i in range(size):
            return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg):
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None


class SimpleSerialTest(unittest.TestCase):
    MAX_TIMESTAMP = 0xFFFFFFFF / 1000

    def setUp(self):
        self.patcher = patch('serial.Serial')
        self.mock_serial = self.patcher.start()
        self.serial_dummy = SerialDummy()
        self.mock_serial.return_value.write = self.serial_dummy.write
        self.mock_serial.return_value.read = self.serial_dummy.read
        self.addCleanup(self.patcher.stop)
        self.bus = SerialBus('bus')

    def tearDown(self):
        self.serial_dummy.reset()

    def test_rx_tx_min_max_data(self):
        """
        Tests the transfer from 0x00 to 0xFF for a 1 byte payload
        """
        for b in range(0, 255):
            msg = can.Message(data=[b])
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertEqual(msg, msg_receive)

    def test_rx_tx_min_max_dlc(self):
        """
        Tests the transfer from a 1 - 8 byte payload
        """
        payload = bytearray()
        for b in range(1, 9):
            payload.append(0)
            msg = can.Message(data=payload)
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertEqual(msg, msg_receive)

    def test_rx_tx_data_none(self):
        """
        Tests the transfer without payload
        """
        msg = can.Message(data=None)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_min_id(self):
        """
        Tests the transfer with the lowest arbitration id
        """
        msg = can.Message(arbitration_id=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_max_id(self):
        """
        Tests the transfer with the highest arbitration id
        """
        msg = can.Message(arbitration_id=536870911)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_max_timestamp(self):
        """
        Tests the transfer with the highest possible timestamp
        """

        msg = can.Message(timestamp=self.MAX_TIMESTAMP)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_max_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (max + 1)
        """
        msg = can.Message(timestamp=self.MAX_TIMESTAMP+1)
        self.assertRaises(ValueError, self.bus.send, msg)

    def test_rx_tx_min_timestamp(self):
        """
        Tests the transfer with the lowest possible timestamp
        """
        msg = can.Message(timestamp=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_min_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (min - 1)
        """
        msg = can.Message(timestamp=-1)
        self.assertRaises(ValueError, self.bus.send, msg)


if __name__ == '__main__':
    unittest.main()
