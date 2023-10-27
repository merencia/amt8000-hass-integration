"""Module for amt-8000 communication."""

import socket

dst_id = [0x00, 0x00]
our_id = [0x8F, 0xFF]
commands = {"auth": [0xF0, 0xF0], "status": [0x0B, 0x4A]}


def calculate_checksum(buffer):
    """Calculate a checksum for a given array of bytes."""
    checksum = 0
    for value in buffer:
        checksum ^= value
    checksum ^= 0xFF
    checksum &= 0xFF
    return checksum


def build_status(data):
    """Build the amt-8000 status from a given array of bytes."""
    length = merge_octets(data[4:6]) - 2
    payload = data[8 : 8 + length]

    model = "AMT-8000" if payload[0] == 1 else "Unknown"

    status = {
        "model": model,
        "version": f"{payload[1]}.{payload[2]}.{payload[3]}",
        "status": get_status(payload),
        "zonesFiring": (payload[20] & 0x8) > 0,
        "zonesClosed": (payload[20] & 0x4) > 0,
        "siren": (payload[20] & 0x2) > 0,
    }

    status["batteryStatus"] = battery_status_for(payload)
    status["tamper"] = (payload[71] & (1 << 0x01)) > 0

    return status


def battery_status_for(resp):
    """Retrieve the battery status."""
    batt = resp[142]
    if batt == 0x01:
        return "dead"
    if batt == 0x02:
        return "low"
    if batt == 0x03:
        return "middle"
    if batt == 0x04:
        return "full"

    return "unknown"


def merge_octets(buf):
    """Merge octets."""
    return buf[0] * 256 + buf[1]


def get_status(payload):
    """Retrieve the current status from a given array of bytes."""
    status = (payload[20] >> 5) & 0x03
    if status == 0x00:
        return "disabled"
    if status == 0x01:
        return "partial_enabled"
    if status == 0x03:
        return "enabled"
    return "unknown"


class CommunicationError(Exception):
    """Exception raised for communication error."""

    def __init__(self, message="Salary is not in (5000, 15000) range"):
        """Initialize the error."""
        self.message = message
        super().__init__(self.message)


class AuthError(Exception):
    """Exception raised for communication error."""

    def __init__(self, message="Salary is not in (5000, 15000) range"):
        """Initialize the error."""
        self.message = message
        super().__init__(self.message)


class Client:
    """Client to communicate with amt-8000."""

    def __init__(self, host, port, device_type=1, software_version=0x10):
        """Initialize the client."""
        self.host = host
        self.port = port
        self.device_type = device_type
        self.software_version = software_version
        self.client = None

    def close(self):
        """Close a connection."""
        if self.client is None:
            raise CommunicationError("Client not connected. Call Client.connect")

        self.client.close()

    def connect(self):
        """Create a new connection."""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))

    def auth(self, password):
        """Create a authentication for the current connection."""
        if self.client is None:
            raise CommunicationError("Client not connected. Call Client.connect")

        pass_array = []
        for char in password:
            if len(password) != 6 or not char.isdigit():
                raise CommunicationError(
                    "Cannot parse password, only 6 integers long are accepted"
                )

            pass_array.append(int(char))

        data = (
            dst_id
            + our_id
            + [0x00, 0x0A]
            + commands["auth"]
            + [self.device_type]
            + pass_array
            + [self.software_version]
        )

        cs = calculate_checksum(data)
        payload = bytes(data + [cs])

        self.client.send(payload)

        return_data = bytearray()

        data = self.client.recv(1024)

        return_data.extend(data)

        result = return_data[8:9][0]

        if result == 0:
            return True
        if result == 1:
            raise AuthError("Invalid password")
        if result == 2:
            raise AuthError("Incorrect software version")
        if result == 3:
            raise AuthError("Alarm panel will call back")
        if result == 4:
            raise AuthError("Waiting for user permission")
        raise CommunicationError("Unknown payload response for authentication")

    def status(self):
        """Return the current status."""
        if self.client is None:
            raise CommunicationError("Client not connected. Call Client.connect")

        status_data = dst_id + our_id + [0x00, 0x02] + commands["status"]
        cs = calculate_checksum(status_data)
        payload = bytes(status_data + [cs])

        return_data = bytearray()
        self.client.send(payload)

        data = self.client.recv(1024)
        return_data.extend(data)

        status = build_status(return_data)
        return status
