#!/usr/bin/env python
import os
import operator
import serial
import serial.tools.list_ports
from time import sleep
from binascii import hexlify

# Contants
NOVA_DEV_TV_SENDING_CARD     = 0x00           # Device type: TV, sending card
NOVA_DEV_RECEIVING_CARD      = 0x01
NOVA_DEV_FUNCTION_CARD       = 0x02

NOVA_CODE_READ               = 0x00           # Indicate read data command
NOVA_CODE_WRITE              = 0x01

class NovaLCT:
    """
        Class for communicate with NovaStar sending card via serial port
    """
    def __init__(self):
        self.serial_baud_rate     = 115200
        self.serial_timeout_sec   = 10                  # number of seconds after which we consider the serial read operation to have failed
        self.serial_number        = 1                   # Index of command (range 1:255)
        self.uart                 = None                # serial port object

    def __init__(self, baud_rate, read_timeout_sec):
        self.serial_baud_rate     = baud_rate
        self.serial_timeout_sec   = read_timeout_sec    # number of seconds after which we consider the serial read operation to have failed
        self.serial_number        = 1                   # Index of command (range 0:255)
        self.uart                 = None                # serial port object

    def __build_request(self, src_addr = 0xFE, dest_addr = 0, dev_type = NOVA_DEV_RECEIVING_CARD, 
                      port_addr = 0, board_addr = 0, code = NOVA_CODE_READ, 
                      reg_addr = 0, data_len = 0, write_data = ''):
        """
            Build request command

            :var int dev_type   : Device type (1 byte)
            :var int reg_addr   : Register address (4 bytes)
            :var int data_len   : Valid data length (2 bytes)
            :var str write_data : Data content to send to device, in hex string (0:N bytes)
            :throw ValueError exception if input data is invalid
            :return
                bytearray : on success.
        """
        checksum = 0x00
        data = "55aa"                                   # Head (2 bytes)
        data += "00"                                    # ACK ( 1 byte)

        data += '{0:02x}'.format(self.serial_number)    # Serial number (1 byte)
        checksum += self.serial_number

        # Source address (1 byte)
        # Address of the computer or sending card that generates and starts the command
        # For computer, the address is fixed to be FE
        data += '{0:02x}'.format(src_addr)
        checksum += src_addr
        
        # Destination address (1 byte)
        # Address of the computer or sending card that the command is to be sent to
        # For computer is FE
        # First device is 00
        data += '{0:02x}'.format(dest_addr)
        checksum += dest_addr

        # Device type (1 byte)
        data += '{0:02x}'.format(dev_type)
        checksum += dev_type
        
        # Port address (1 byte)
        # RJ45 output port address of the sending card: 0, 1, 2, 3
        data += '{0:02x}'.format(port_addr)
        checksum += port_addr
        
        # Board address (2 bytes)
        # Address of a device connected in daisy chain on a CAT5 data cable: 0, 1, 2, 3,..
        data += '{0:02x}'.format(board_addr & 0xFF)
        checksum += board_addr & 0xFF

        data += '{0:02x}'.format(board_addr >> 8)
        checksum += board_addr >> 8

        # Code (1 byte)
        # Specify read, write command
        data += '{0:02x}'.format(code)
        checksum += code

        # Reserved (1 byte)
        data += '00'

        # Register unit address (4 bytes)
        number = reg_addr & 0xFF
        data += '{0:02x}'.format(number)
        checksum += number

        number = (reg_addr >> 8) & 0xFF
        data += '{0:02x}'.format(number)
        checksum += number

        number = (reg_addr >> 16) & 0xFF
        data += '{0:02x}'.format(number)
        checksum += number

        number = (reg_addr >> 24) & 0xFF
        data += '{0:02x}'.format(number)
        checksum += number

        if code == NOVA_CODE_READ:
            # Valid data length (2 bytes)
            number = data_len & 0xFF
            data += '{0:02x}'.format(number)
            checksum += number

            number = data_len >> 8
            data += '{0:02x}'.format(number)
            checksum += number
        else:
            # Rase exception if there is no given data
            if write_data == None or write_data == '':
                raise ValueError('Argument exception: write_data cannot be null or empty')

            # Automatic append 0 to first position
            if (len(write_data) % 2) != 0:
                write_data = '0' + write_data

            data_len = len(write_data)/2

            # Valid data length (2 bytes)
            number = data_len & 0xFF
            data += '{0:02x}'.format(number)
            checksum += number

            number = data_len >> 8
            data += '{0:02x}'.format(number)
            checksum += number

            # Write data (0:N bytes)
            for i in range(0, len(write_data), 2):
                number = int(write_data[i:i+2], 16)
                data += '{0:02x}'.format(number)
                checksum += number

        # Checkout (2 bytes)
        checksum += 0x5555

        number = checksum & 0xFF
        data += '{0:02x}'.format(number)

        number = checksum >> 8
        data += '{0:02x}'.format(number)

        # Increase command index
        self.serial_number += 1
        if self.serial_number > 255:
            self.serial_number = 1
        
        return bytearray.fromhex(data)

    def __parse_response(self, read_bytes):
        """
            Parse response data from sending card to computer

            :var bytearray read_bytes: response data from device
            :return
                (data,..) : on success.
                (errcode, msg): on failed.
        """
        strdata = hexlify(read_bytes)
        strdata = strdata.lower()

        if len(strdata) < 40:
            return (1, 'Argument exception: input data is less than minimum length of 20 bytes')

        checksum = 0x00

        # Head (2 bytes)
        strvalue = strdata[0:4]
        strdata = strdata[4:]
        if strvalue != 'aa55':
            return (2, 'Invalid acknowledge data: head')

        # ACK ( 1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        ack_num = int(strvalue, 16)
        checksum += ack_num

        if ack_num == 0x00:
            pass
        elif ack_num == 0x01:
            return (3, 'Command failed due to timeout')
        elif ack_num == 0x02:
            return (4, 'Command failed due to check error on request data package')
        elif ack_num == 0x03:
            return (5, 'Command failed due to check error on acknowledge data package')
        elif ack_num == 0x04:
            return (6, 'Command failed due to invalid command')
        elif ack_num >= 0x05:
            return (7, 'Command failed due to invalid ack code')
        
        # Serial number (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        serial_number = int(strvalue, 16)
        checksum += serial_number

        # Source address (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        src_addr = int(strvalue, 16)
        checksum += src_addr

        # Destination address (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        dest_addr = int(strvalue, 16)
        checksum += dest_addr

        # Device type (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        dev_type = int(strvalue, 16)
        checksum += dev_type

        # Port address (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        port_addr = int(strvalue, 16)
        checksum += port_addr

        # Board address (2 bytes)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        low_byte = int(strvalue, 16)
        checksum += low_byte
        
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        high_byte = int(strvalue, 16)
        checksum += high_byte

        board_addr = (high_byte << 8) | low_byte

        # Code (1 byte)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        code = int(strvalue, 16)
        checksum += code

        # Reserved (1 byte)
        strdata = strdata[2:]

        # Register unit address (4 bytes)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        byte1 = int(strvalue, 16)
        checksum += byte1
        
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        byte2 = int(strvalue, 16)
        checksum += byte2

        strvalue = strdata[0:2]
        strdata = strdata[2:]
        byte3 = int(strvalue, 16)
        checksum += byte3

        strvalue = strdata[0:2]
        strdata = strdata[2:]
        byte4 = int(strvalue, 16)
        checksum += byte4

        reg_addr = (byte4 << 24) | (byte3 << 16) | (byte2 << 8) | byte1

        # Valid data length (2 bytes)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        low_byte = int(strvalue, 16)
        checksum += low_byte
        
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        high_byte = int(strvalue, 16)
        checksum += high_byte

        data_len = (high_byte << 8) | low_byte

        if code == NOVA_CODE_WRITE and data_len > 0:
            return (4, 'Data length cannot be greater than 0 when code is write command')
        
        if code == NOVA_CODE_READ and data_len == 0:
            return (4, 'Data length cannot be equals to 0 when code is read command')
        
        # Response data in hex string 0:N
        res_data = ''

        if data_len != ((len(strdata) - 4) / 2):
            return (5, 'Data length does not match with remain data length')
        
        if data_len > 0:
            for i in range(0, data_len):
                strvalue = strdata[0:2]
                strdata = strdata[2:]
                number = int(strvalue, 16)
                res_data += '{0:02x}'.format(number)
                checksum += number

        checksum += 0x5555

        # Checkout (2 bytes)
        strvalue = strdata[0:2]
        strdata = strdata[2:]
        low_byte = int(strvalue, 16)
        
        strvalue = strdata[0:2]
        high_byte = int(strvalue, 16)

        checkout = (high_byte << 8) | low_byte

        if checksum != checkout:
            return (6, 'Data checksum does not match')
        
        return (serial_number, src_addr, dest_addr, dev_type, port_addr, board_addr, code, reg_addr, data_len, res_data)

    def get_serial_ports(self):
        """
            List all available serial ports

            :return
                list[ListPortInfo]: A list of serial port info
        """
        list_ports = list(serial.tools.list_ports.comports())               # get all available serial ports
        ports = [port for port in list_ports if port[2] != 'n/a']           # remove all unfit serial ports
        ports.sort(key=operator.itemgetter(1))                              # sort the list based on the port
        return ports

    def select_serial_port(self, ports):
        """
            Select a serial port based on given list with condition to match
            with Nova LED module

            :var list(ListPortInfo) ports: A list of serial port info
            :return
                ListPortInfo: a best matched port
        """
        if ports == None or len(ports) == 0:
            raise ValueError('Input serial ports cannot be none or empty')

        for port in ports:
            (_, _, hwid) = port
            if hwid.find("VID:PID=10C4:EA60") > -1:
                return port

        for port in ports:
            (_, description, _) = port
            if description.find("USB to UART") > -1:
                return port
            if description.find("CP210") > -1:
                return port
        
        print("[WARN] No available ports that matched with pattern. Use first port, instead")
        return port[0]

    def open_serial_port(self, port):
        """
            Open serial port with preset configuration

            :var ListPortInfo port: serial port info
            :return
                Serial: on success.
        """
        if port == None:
            raise ValueError('Port cannot be null')
        
        if not hasattr(port, "name"):
            raise ValueError('Invalid uart port')

        port_name = port.name
        if not port_name.startswith('/dev/'):
            port_name = '/dev/' + port_name
        
        self.uart = serial.Serial(
            port = port_name,
            baudrate = self.serial_baud_rate,
            timeout  = self.serial_timeout_sec,
            bytesize = serial.EIGHTBITS,
            parity   = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
        )
        return self.uart
    
    def open(self):
        """ 
            Open connection to serial port
        """
        ports = self.get_serial_ports()
        port = self.select_serial_port(ports)
        self.uart = self.open_serial_port(port)
        self.serial_number = 0x01

    def reopen(self):
        """
            Re-open connection to serial port, if needed
        """
        if self.uart == None:
            self.open()

    def close(self):
        """
            Close openned serial port
        """
        try:
            if self.uart == None:
                return

            self.uart.close()
        except ValueError as ex:
            print("[ERR ] Unable to close serial port: %s" % ex.strerror)
        except serial.SerialException as ex:
            print("[ERR ] Unable to close serial port. Error(%s): %s" % (ex.errno, ex.strerror))
        except:
            print("[ERR ] Unable to close serial port")

    def write(self, dev_type, reg_addr, write_data, data_len = 0, dest_addr = 0, port_addr = 0, board_addr = 0):
        """
            Write data to led controller register and return response from the device

            :var int dev_type   : Device type (1 byte)
            :var int reg_addr   : Register address (4 bytes)
            :var str write_data : Data content to send to device, in hex string (0:N bytes)
        """
        if self.uart == None:
            raise RuntimeError('Serial port is not openned yet')

        src_addr = 0xFE
        code = NOVA_CODE_WRITE

        request = self.__build_request(src_addr, dest_addr, dev_type, port_addr, board_addr, code, reg_addr, data_len, write_data)
        self.uart.write(request)

        resp_bytes = self.uart.read()
        if len(resp_bytes) == 0:
            raise RuntimeError('No response from serial port')

        sleep(0.2)
        remain_bytes = self.uart.inWaiting()
        resp_bytes += self.uart.read(remain_bytes)
        resp_parsed = self.__parse_response(resp_bytes)

        if isinstance(resp_parsed, tuple) and len(resp_parsed) == 2:
            raise RuntimeError('Write to device failed. Error(%s): %s' % (resp_parsed[0], resp_parsed[1]))
        
        return resp_parsed

    def read(self, dev_type, reg_addr, data_len, dest_addr = 0, port_addr = 0, board_addr = 0):
        """
            Read data from led controller register
            
            :var int dev_type   : Device type (1 byte)
            :var int reg_addr   : Register address (4 bytes)
            :var int data_len   : Length of data want to read (in bytes)

            :return
                tuple           : contains data struct information of response
        """
        if self.uart == None:
            raise RuntimeError('Serial port is not openned yet')

        src_addr = 0xFE
        code = NOVA_CODE_READ

        request = self.__build_request(src_addr, dest_addr, dev_type, port_addr, board_addr, code, reg_addr, data_len, write_data= '')
        self.uart.write(request)

        resp_bytes = self.uart.read()
        if len(resp_bytes) == 0:
            raise RuntimeError('No response from serial port')

        sleep(0.2)
        remain_bytes = self.uart.inWaiting()
        resp_bytes += self.uart.read(remain_bytes)
        resp_parsed = self.__parse_response(resp_bytes)

        if isinstance(resp_parsed, tuple) and len(resp_parsed) == 2:
            raise RuntimeError('Read from device failed. Error(%s): %s' % (resp_parsed[0], resp_parsed[1]))
        
        return resp_parsed

    def read_receiving_card_id_model(self):
        """ 
            Read the receiving card model id

            :return
                str     : string OK if success or error message if failed
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x00000000, data_len= 0x02)
        if data_len != 2:
            raise RuntimeError('Invalid data length in response from device')

        if res_data == '0141':
            return 'OK'
        
        raise RuntimeError('Unknown model id: ' + res_data)

    def read_sending_card_id_model(self):
        """ 
            Read the sending card/controller model id

            :return
                str     : string contains name of the device or error if failed
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_TV_SENDING_CARD, reg_addr= 0x00000002, data_len= 0x02)
        if data_len != 2:
            raise RuntimeError('Invalid data length in response from device')
        
        if res_data == '0101':
            return 'MCRL500'
        if res_data == '0100':
            return 'MSD300/MCTRL300'
        if res_data == '0111':
            return 'MSD600/MCTRL600/MCTRL610'
        
        raise RuntimeError('Unknown model id: ' + res_data)

    def read_function_card_id_model(self):
        """ 
            Read the function card model id

            :return
                str     : string contains name of the device or error if failed
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_FUNCTION_CARD, reg_addr= 0x00000002, data_len= 0x02)
        if data_len != 2:
            raise RuntimeError('Invalid data length in response from device')
        
        if res_data == '0181':
            return 'MFN300'
        
        raise RuntimeError('Unknown model id: ' + res_data)

    def read_temperature_receiving_card(self):
        """
            Read temperature on receiving card

            :return
                float   : Temperature value (celcius degree)
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x0a000000, data_len= 0x02)
        if data_len != 2:
            raise RuntimeError('Invalid data length in response from device')
        
        head = int(res_data[0:2], 16)
        if (head & 0x80) == 0x00:
            raise RuntimeError('Response temperature is invalid')
        
        # Temperature negative or positive
        sign = 1
        if (head & 0x01) == 0x01:
            sign = -1
        
        temperature = int(res_data[2:4], 16)
        temperature = sign * 0.5 * temperature
        return temperature

    def read_receiving_card_voltage(self):
        """
            Read voltage on receiving card

            :return
                float   : Volgate value (V)
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x0a000003, data_len= 0x01)
        if data_len != 1:
            raise RuntimeError('Invalid data length in response from device')
        
        volt = int(res_data, 16)
        if (volt & 0x80) == 0x00:
            raise RuntimeError('Response voltage is invalid')

        volt = volt & 0x7F
        volt = 0.1 * volt
        return volt

    def read_sending_card_video_signal(self):
        """ 
            DVI signal check on sending card

            :return
                True : DVI signal is good.
                False: No VDI signal
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_TV_SENDING_CARD, reg_addr= 0x02000017, data_len= 0x01)
        if data_len != 1:
            raise RuntimeError('Invalid data length in response from device')
        
        if res_data.lower() == '01':
            return True
        return False

    def read_brightness(self):
        """
            Read brightness on receiving card

            :return
                int   : Brightness value (0:255)
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x02000001, data_len= 0x01)
        if data_len != 1:
            raise RuntimeError('Invalid data length in response from device')
        
        return int(res_data, 16)

    def write_brightness(self, value):
        """
            Write brightness to receiving card

            :var int value   : Brightness value (0:255)
        """
        if ((value < 0) or (value > 255)):
            raise RuntimeError("Input value must be in range 0:255")

        data = '{0:02x}'.format(value)
        self.write(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x02000001, write_data= data)

    def is_monitor_card_attached(self):
        """ 
            Detect whether monitor card is attached to receving card or not

            :return
                True : Monitor card is attached.
                False: Monitor card is dettached.
        """
        (_, _, _, _, _, _, _, _, data_len, res_data) = self.read(dev_type= NOVA_DEV_RECEIVING_CARD, reg_addr= 0x0a000020, data_len= 0x01)
        if data_len != 1:
            raise RuntimeError('Invalid data length in response from device')
        
        if res_data.lower() == 'ff':
            return True
        return False

#---------------------------
# Test functions
#---------------------------
# novalct = NovaLCT(baud_rate= 115200, read_timeout_sec = 10)

# print('List of serial ports: ')
# ports = novalct.get_serial_ports()
# for port in ports:
#     (name, des, hwid) = port
#     print(' - %s, %s, %s' % (name, des, hwid))

# novalct.open()

# result = novalct.read_sending_card_id_model()
# print('Sending card model: %s' % result)

# result = novalct.read_receiving_card_id_model()
# print('Receiving card model: %s' % result)

# result = novalct.read_temperature_receiving_card()
# print('Receiving card temperature: %s' % result)

# # result = novalct.read_function_card_id_model()
# # print('Function card model: %s' % result)

# result = novalct.is_monitor_card_attached()
# print('Is monitor card attached: %s' % result)

# result = novalct.read_sending_card_video_signal()
# if result == True:
#     print('DVI signal checking: good')
# else:
#     print('DVI signal checking: no signal')

# result = novalct.read_brightness()
# print('Receiving card brightness: %s' % result)

# novalct.write_brightness(69)
# print('Write brightness to receiving card...')

# result = novalct.read_brightness()
# print('Receiving card brightness: %s' % result)

# novalct.close()
