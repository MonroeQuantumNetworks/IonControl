"""Pythonic wrapper around the Cambridge Instruments CW Signal Generator DLL."""
import xmlrpclib
import SimpleXMLRPCServer

from ThinInterface import CICW_ThinInterface, read_error

##
# Public Functions
#

def get_local_slot(name, dll_path = None):
    """Return a Slot object representing a specific connection to a VISA
    resource.

    name -- The VISA resource name. e.g. PXI32::0::INSTR

    dll_path -- If given, the location to look for the DLL. If not,
    use the default from ThinInterface.CICW_ThinInterface.

    Return a Slot object.
    """
    interface = CICW_ThinInterface.get_dll(dll_path)
    return Slot(interface, name)

def get_remote_slot(name, address):
    """Return a Slot object representing a connection to a VISA resource
    on a remote computer. The remote computer must be running an
    XML-RPC server exporting all the DLL's functions.

    name -- The VISA resource name. e.g. PXI32::0::INSTR

    address -- A string describing the server's address.

    Return a Slot object
    """
    try:
        interface = xmlrpclib.ServerProxy(address)
    except Exception as e:
        raise ValueError('Cannot start up a connection with address {}: {}'.format(address, e))

    try:
        slot = Slot(interface, name)
    except Exception as e:
        raise ValueError('Server connection worked, but a Slot could not be made from it: {}'.format(e))

    return slot

def start_server(local_address, dll_path = None):
    """Start a server running that other clients may connect to with
    get_remote_slot. This function will never return.

    local_address -- The address to pass to the server. See
    SimpleXMLRPCServer's documentation, but one example is
    ("localhost", 8000) to bind to the localhost interface on port
    8000.

    dll_path -- If given, the location to look for the DLL. If not,
    use the default from ThinInterface.CICW_ThinInterface.

    """
    make_rpc_server(local_address, dll_path).server_forever()

##
# Stuff you don't normally need to use directly
# 

def make_rpc_server(local_address, dll_path = None):
    """Create and return, but do not start, an RPC server.

    local_address -- The address to pass to the server. See
    SimpleXMLRPCServer's documentation, but one example is
    ("localhost", 8000) to bind to the localhost interface on port
    8000.

    dll_path -- If given, the location to look for the DLL. If not,
    use the default from ThinInterface.CICW_ThinInterface.
    """
    try:
        server = SimpleXMLRPCServer.SimpleXMLRPCServer(local_address)
    except Exception as e:
        raise ValueError('Could not create a server at address {}: {}'.format(local_address, e))
    try:
        interface = CICW_ThinInterface.get_dll(dll_path)
    except Exception as e:
        raise ValueError('Could not create an interface to the DLL: {}'.format(e))

    try:
        server.register_instance(interface)
    except Exception as e:
        raise ValueError('Could not register the CICW_ThinInterface instance with the RPC server: {}'.format(e))
    return server

class CICWException(Exception):
    def __init__(self, code_string):
        self._code_string = code_string
    def __str__(self):
        return str(self._code_string)

def process_status(status):
    """Given a status code, either do nothing or throw an exception."""
    if status != 0:
        raise CICWException(read_error(status))

class CICW_Meta(type):
    """Metaclass to add docstrings to all CICW objects so I don't have to
    retype them. Don't worry about how this works."""

    def __init__(cls, name, bases, dct):
        for attrname, attrvalue in dct.iteritems():
            normalized_name = attrname.replace('_','').lower()
            if callable(attrvalue) and attrvalue.__doc__ is None:
                # We iterate instead of looking up since we can
                # normalize by turning to lower case.
                for othername, value in CICW_ThinInterface.__dict__.iteritems():
                    if othername.lower() == normalized_name:
                        attrvalue.__doc__ = value.__doc__
        return super(CICW_Meta, cls).__init__(name, bases, dct)

class Board(object):
    """This class should be rarely used. It exists only because the Close
    function exported by the DLL does not take a slot argument."""

    __metaclass__ = CICW_Meta

    def __init__(self, interface):
        self._interface = interface

    def close(self):
        self._interface.close()

class Slot(object):
    """The primary class of interaction. Each Slot class corresponds to a
    call to CICW_RevC_Init in the DLL."""

    __metaclass__ = CICW_Meta

    MAX_CHANNELS = 2

    def __init__(self, interface, name):
        self._interface = interface
        status, slot_number = self._interface.Init(name)
        process_status(status)
        self._slot_number = slot_number
        self._channels = [Channel(self._interface, self, c) for c in range(self.MAX_CHANNELS)]
        self._board = Board(self._interface)

    @property
    def slot_number(self):
        return self._slot_number

    def board(self):
        """Return the Board class for this Slot"""
        # This is not a property to mimic the interface for channel,
        # which must take an argument.
        return self._board

    def channel(self, channel):
        """Return the given channel for this Slot.

        channel -- An integer identifying the channel

        Return a Channel object.

        Note: This will not throw an error if an incorrect channel is
        used. That will occur at first usage.
        """
        try:
            return self._channels[channel]
        except:
            raise ValueError('channel must be between 0 and {}'.format(self.MAX_CHANNELS))

    def reset_card(self):
        status = self._interface.ResetCard(self.slot_number)
        process_status(status)

class Channel(object):
    """A class representing a channel on the device. All functions that
    have a channel argument are found here."""

    __metaclass__ = CICW_Meta

    def __init__(self, interface, slot, channel):
        """Create a new Channel.

        interface -- The CICW_ThinInterface or similar interface.

        slot -- The slot object this channel belongs to.

        channel -- The index of this channel.
        """
        self._interface = interface
        self._slot = slot
        self._slot_number = slot._slot_number
        self._channel = channel

    def board(self):
        return self.slot().board()

    def slot(self):
        return self._slot

    def signal_locked(self):
        status, locked = self._interface.SignalLocked(self._slot_number, self._channel)
        process_status(status)
        return locked

    def get_output_enabled(self):
        status, enabled = self._interface.GetOutputEnabled(self._slot_number, self._channel)
        process_status(status)
        return enabled

    def set_output_enabled(self, enabled):
        status = self._interface.GetOutputEnabled(self._slot_number, self._channel, enabled)
        process_status(status)

    def disable_output(self):
        status = self._interface.DisableOutput(self._slot_number, self._channel)
        process_status(status)

    def select_clock(self, clock_src, clock_mhz):
        status = self._interface.SelectClock(self._slot_number, self._channel, clock_src, clock_mhz)
        process_status(status)

    def get_clock(self):
        status, ref_clock = self._interface.GetClock(self._slot_number, self._channel)
        process_status(status)
        return ref_clock

    def get_clock_mhz(self):
        status, clock_mhz = self._interface.GetClockMHz(self._slot_number, self._channel)
        process_status(status)
        return clock_mhz

    def get_ext_ref_mhz(self):
        status, clock_mhz = self._interface.GetExtRefMHz(self._slot_number, self._channel)
        process_status(status)
        return clock_mhz

    def get_ref_divider(self):
        status, ref_divider = self._interface.GetRefDivider(self._slot_number, self._channel)
        process_status(status)
        return ref_divider

    def set_ref_divider(self, ref_divider):
        status = self._interface.SetRefDivider(self._slot_number, self._channel, ref_divider)
        process_status(status)

    def get_board_id_string(self):
        status, board_id = self._interface.GetBoardIDString(self._slot_number, self._channel)
        process_status(status)
        return board_id

    def get_card_type(self):
        status, card_type = self._interface.GetCardType(self._slot_number, self._channel)
        process_status(status)
        return card_type

    def get_firmware_rev(self):
        status, fw_rev = self._interface.GetFirmwareRev(self._slot_number, self._channel)
        process_status(status)
        return fw_rev

    def get_serial_number(self):
        status, serial = self._interface.GetSerialNumber(self._slot_number, self._channel)
        process_status(status)
        return serial

    def get_temperature(self):
        status, temp_c = self._interface.GetTemperature(self._slot_number, self._channel)
        process_status(status)
        return temp_c

    def get_card_rev(self):
        status, card_rev = self._interface.GetCardRev(self._slot_number, self._channel)
        process_status(status)
        return card_rev

    def set_frequency_attn(self):
        status = self._interface.SetFrequencyAttn(self._slot_number, self._channel)
        process_status(status)

    def get_fdac(self, freq_mhz):
        status, fdac = self._interface.GetFDAC(self._slot_number, self._channel, freq_mhz)
        process_status(status)
        return freq_mhz

    def get_pdac(self):
        status, pdac = self._interface.GetPDAC(self._slot_number, self._channel)
        process_status(status)
