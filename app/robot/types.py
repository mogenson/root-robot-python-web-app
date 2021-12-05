from dataclasses import dataclass
from enum import Enum
from struct import unpack

from .packet import Packet


@dataclass
class Bumper:
    left: bool
    right: bool

    @classmethod
    def from_packet(cls, packet: Packet):
        return Bumper(packet.payload[4] & 0x80 != 0, packet.payload[4] & 0x40 != 0)


@dataclass
class Color:
    WHITE = 0
    BLACK = 1
    RED = 2
    GREEN = 3
    BLUE = 4
    ORANGE = 5
    YELLOW = 6
    MAGENTA = 7
    NONE = 15
    ANY = -1

    colors: list[int]

    @classmethod
    def from_packet(cls, packet: Packet):
        return Color([c >> i & 0xF for c in packet.payload for i in range(4, -1, -4)])


@dataclass
class Light:
    DARKER = 4
    RIGHT_BRIGHTER = 5
    LEFT_BRIGHTER = 6
    LIGHTER = 7

    state: int
    left: int = 0
    right: int = 0

    @classmethod
    def from_packet(cls, packet: Packet):
        return Light(
            packet.payload[4],
            unpack(">H", packet.payload[5:7])[0],
            unpack(">H", packet.payload[7:9])[0],
        )


@dataclass
class Touch:
    front_left: bool
    front_right: bool
    back_right: bool
    back_left: bool

    @classmethod
    def from_packet(cls, packet: Packet):
        return Touch(
            packet.payload[4] & 0x80 != 0,
            packet.payload[4] & 0x40 != 0,
            packet.payload[4] & 0x20 != 0,
            packet.payload[4] & 0x10 != 0,
        )


def note(note: str, A4=440) -> float:
    """Convert a note name into frequency in hertz: eg. 'C#5'"""
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = int(note[-1])
    step = notes.index(note[0:-1])
    step += ((octave - 1) * 12) + 1
    return A4 * 2 ** ((step - 46) / 12)


class Marker(Enum):
    UP = 0
    DOWN = 1
    ERASE = 2


class Animation(Enum):
    OFF = 0
    ON = 1
    BLINK = 2
    SPIN = 3


class ColorSensors(Enum):
    SENSORS_0_TO_7 = 0
    SENSORS_8_TO_15 = 1
    SENSORS_16_TO_23 = 2
    SENSORS_24_TO_31 = 3


class ColorLighting(Enum):
    OFF = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    ALL = 4


class ColorFormat(Enum):
    ADC_COUNTS = 0
    MILLIVOLTS = 1


class ModulationType(Enum):
    DISABLED = 0
    VOLUME = 1
    PULSE_WIDTH = 2
    FREQUENCY = 3
