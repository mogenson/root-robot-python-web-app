from asyncio import get_running_loop
from collections import defaultdict
from struct import pack, unpack

from ..debug import debug
from .packet import Packet
from .types import *


class Robot:
    """
    Object to control Bluetooth connected robot. Use `on_` decorators to
    register event handlers. Use other methods to send commands to robot and
    wait for response. Don't forget to await async methods!
    """

    def __init__(self, bluetooth):
        self._bluetooth = bluetooth
        self._bluetooth.data_received_callback = self._data_received
        self._loop = get_running_loop()
        self._responses = {}
        self._events = defaultdict(list)
        self._tasks = {}
        self._inc = 0
        self._running = False
        self._enable_motors = True

    def on_color(self, filter: Color = None):
        """
        Decorator for event handler of type: async callback(color: Color) Use
        default None filter to pass every event. Set filter to an instance of
        Color() to only pass events that match filter. Use Color.ANY for any
        color. Color.colors length can be from 1 to 32.
        """

        def decorator(callback):
            def filter_function(packet):
                color = Color.from_packet(packet)
                if not filter:
                    return color
                # get size of each zone
                chunk = round(len(color.colors) / len(filter.colors))
                # chop color list into zones
                zones = [
                    color.colors[i : i + chunk]
                    for i in range(0, len(color.colors), chunk)
                ]
                # check if filter color exists in each zone (or is ANY)
                result = map(
                    lambda x: x[0] == Color.ANY or x[0] in x[1],
                    zip(filter.colors, zones),
                )
                return color if all(result) else None

            self._events[(4, 2)].append((filter_function, callback))

        return decorator

    def on_bump(self, filter: Bumper = None):
        """
        Decorator for event handler of type: async callback(bumper: Bumper)
        Use default None filter to pass every event. Set filter to an instance
        of Bumper() to only pass events that match filter.
        """

        def decorator(callback):
            def filter_function(packet):
                bumper = Bumper.from_packet(packet)
                return bumper if not filter or filter == bumper else None

            self._events[(12, 0)].append((filter_function, callback))

        return decorator

    def on_light(self, filter: Light = None):
        """
        Decorator for event handler of type: async callback(light: Light)
        Use default None filter to pass every event. Set filter to an instance
        of Light() to only pass events that match Light state.
        """

        def decorator(callback):
            def filter_function(packet):
                light = Light.from_packet(packet)
                return light if not filter or filter.state == light.state else None

            self._events[(13, 0)].append((filter_function, callback))

        return decorator

    def on_touch(self, filter: Touch = None):
        """
        Decorator for event handler of type: async callback(touch: Touch)
        Use default None filter to pass every event. Set filter to an instance
        of Touch() to only pass events that match filter.
        """

        def decorator(callback):
            def filter_function(packet):
                touch = Touch.from_packet(packet)
                return touch if not filter or filter == touch else None

            self._events[(17, 0)].append((filter_function, callback))

        return decorator

    async def get_versions(self, board: int) -> list[int]:
        """Get version numbers. Returns [board, fw maj, fw min, hw maj, hw min,
        boot maj, boot min, proto maj, proto min]"""
        dev, cmd, inc = 0, 0, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc, bytes([board])))
        packet = await future
        return packet.payload[:9] if packet else []

    async def set_name(self, name: str):
        """Set robot name"""
        utf = name.encode("utf-8")
        while len(utf) > Packet.PAYLOAD_LEN:
            name = name[:-1]
            utf = name.encode("utf-8")
        await self.write_packet(Packet(0, 1, self.inc, utf))

    async def get_name(self) -> str:
        """Get robot name"""
        dev, cmd, inc = 0, 2, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc))
        packet = await future
        return packet.payload.decode("utf-8").rstrip("\0") if packet else ""

    async def set_speeds(self, left: float, right: float):
        """Set motor speed in cm/s"""
        if self._enable_motors:
            left = self.bound(int(left * 10), -100, 100)
            right = self.bound(int(right * 10), -100, 100)
            await self.write_packet(Packet(1, 4, self.inc, pack(">ii", left, right)))

    async def set_left_speed(self, speed: float):
        """Set left motor speed in cm/s"""
        if self._enable_motors:
            speed = self.bound(int(speed * 10), -100, 100)
            await self.write_packet(Packet(1, 6, self.inc, pack(">i", speed)))

    async def set_right_speed(self, speed: float):
        """Set right motor speed in cm/s"""
        if self._enable_motors:
            speed = self.bound(int(speed * 10), -100, 100)
            await self.write_packet(Packet(1, 7, self.inc, pack(">i", speed)))

    async def drive_distance(self, distance: float):
        """Drive distance in centimeters"""
        if self._enable_motors:
            dev, cmd, inc = 1, 8, self.inc
            packet = Packet(dev, cmd, inc, pack(">i", int(distance * 10)))
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(packet)
            await future

    async def turn_right(self, angle: float):
        """Rotate clockwise in degrees"""
        if self._enable_motors:
            dev, cmd, inc = 1, 12, self.inc
            packet = Packet(dev, cmd, inc, pack(">i", int(angle * 10)))
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(packet)
            await future

    async def turn_left(self, angle: float):
        """Rotate counter-clockwise in degrees"""
        await self.turn_right(-angle)

    async def reset_position(self):
        """Reset robot's position estimate to zero"""
        await self.write_packet(Packet(1, 15, self.inc))

    async def get_position(self) -> tuple[float, float, float]:
        """Get robot's position estimate. Returns (x, y, heading) in cm and
        degrees"""
        dev, cmd, inc = 1, 16, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc))
        packet = await future
        return (
            tuple([p / 10 for p in unpack(">3h", packet.payload[4:10])])
            if packet
            else (0, 0, 0)
        )

    async def arc(self, angle: float, radius: float):
        """Drive arc defined by angle in degrees and radius in cm"""
        if self._enable_motors:
            dev, cmd, inc = 1, 27, self.inc
            payload = pack(">ii", int(angle * 10), int(radius * 10))
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(Packet(dev, cmd, inc, payload))
            await future

    async def set_marker(self, position: int):
        """Set marker to position of type Marker"""
        if self._enable_motors:
            dev, cmd, inc = 2, 0, self.inc
            payload = bytes([self.bound(position, Marker.UP, Marker.ERASE)])
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(Packet(dev, cmd, inc, payload))
            await future

    async def set_lights(
        self, red: int, green: int, blue: int, animation: int = Animation.ON
    ):
        """Set LED cross to animation of type Animation with color red, green,
        blue"""
        animation = self.bound(animation, Animation.OFF, Animation.SPIN)
        red = self.bound(red, 0, 255)
        green = self.bound(green, 0, 255)
        blue = self.bound(blue, 0, 255)
        payload = bytes([animation, red, green, blue])
        await self.write_packet(Packet(3, 2, self.inc, payload))

    async def get_color_sensor_data(
        self, bank: int, lighting: int, format: int
    ) -> list[int]:
        """Get color data for bank of type ColorSensors, lighting of type
        ColorLighting, and format of type ColorFormat. Returns list of 8
        values"""
        bank = self.bound(
            bank, ColorSensors.SENSORS_0_TO_7, ColorSensors.SENSORS_24_TO_31
        )
        lighting = self.bound(lighting, ColorLighting.OFF, ColorLighting.ALL)
        format = self.bound(format, ColorFormat.ADC_COUNTS, ColorFormat.MILLIVOLTS)
        dev, cmd, inc = 4, 1, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc, bytes([bank, lighting, format])))
        packet = await future
        return list(unpack(">8H", packet.payload)) if packet else []

    async def play_note(self, frequency: float, duration: float):
        """Play note with frequency in hertz for duration in seconds"""
        dev, cmd, inc = 5, 0, self.inc
        payload = pack(">IH", abs(int(frequency)), abs(int(duration * 1000)))
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc, payload))
        await future

    async def stop_playing_note(self):
        """Stop currently playing note"""
        await self.write_packet(Packet(5, 1, self.inc))

    async def say(self, phrase: str):
        """Say a phrase in robot language"""
        buf = phrase.encode("utf-8")
        for payload in [
            buf[i : i + Packet.PAYLOAD_LEN]
            for i in range(0, len(buf), Packet.PAYLOAD_LEN)
        ]:
            dev, cmd, inc = 5, 4, self.inc
            future = self._loop.create_future()
            self._responses[(dev, cmd, inc)] = future
            await self.write_packet(Packet(dev, cmd, inc, payload))
            await future

    async def play_sweep(
        self,
        start_frequency: float,
        end_frequency: float,
        duration: float,
        attack: float = 0,
        release: float = 0,
        volume: float = 1.0,
        modulation_type: int = ModulationType.DISABLED,
        modulation_rate: int = 0,
        append: bool = False,
    ):
        """Play sweep with start and end frequency in hertz, duration in
        seconds, attack and release envelope in seconds, volume from 0 to 1.0,
        modulation type of ModulationType, and modulation rate in hertz. Set
        append to play this sweep after current sweep has finished."""
        dev, cmd, inc = 5, 5, self.inc
        start_frequency = abs(int(start_frequency * 1000))
        end_frequency = abs(int(end_frequency * 1000))
        duration = abs(int(duration * 1000))
        attack = self.bound(int(attack * 1000), 0, 255)
        release = self.bound(int(release * 1000), 0, 255)
        volume = self.bound(int(volume * 255), 0, 255)
        modulation_type = self.bound(
            modulation_type, ModulationType.DISABLED, ModulationType.FREQUENCY
        )
        modulation_rate = self.bound(modulation_rate, 0, 255)
        payload = pack(
            ">IIH6B",
            start_frequency,
            end_frequency,
            duration,
            attack,
            release,
            volume,
            modulation_type,
            modulation_rate,
            append,
        )
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc, payload))
        await future

    async def stop_saying(self):
        """Stop current phrase"""
        await self.stop_playing_note()

    async def get_light_sensor_data(self) -> tuple[int, int]:
        """Get light sensor data. Returns (left_mV, right_mV)"""
        dev, cmd, inc = 13, 1, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc))
        packet = await future
        return unpack(">2H", packet.payload[4:8]) if packet else (0, 0)

    async def get_battery_level(self) -> tuple[int, int]:
        """Get battery level. Returns (mV, percent)"""
        dev, cmd, inc = 14, 1, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc))
        packet = await future
        return (
            (unpack(">H", packet.payload[4:6])[0], packet.payload[6])
            if packet
            else (0, 0)
        )

    async def get_accelerometer(self) -> tuple[float, float, float]:
        """Get accelerometer data. Returns (x, y, z) in g"""
        dev, cmd, inc = 16, 1, self.inc
        future = self._loop.create_future()
        self._responses[(dev, cmd, inc)] = future
        await self.write_packet(Packet(dev, cmd, inc))
        packet = await future
        return (
            tuple([a / 1000 for a in unpack(">3h", packet.payload[4:10])])
            if packet
            else (0, 0, 0)
        )

    @property
    def inc(self):
        """Access then increment wrapping ID"""
        inc = self._inc
        self._inc += 1
        if self._inc > 255:
            self._inc = 0
        return inc

    @staticmethod
    def bound(value, low, high):
        """Constrain value between low and high"""
        return min(high, max(low, value))

    async def run(self):
        """Enable the event handlers and robot communication"""
        self._responses = {}
        self._events = defaultdict(list)
        self._tasks = {}
        # on stop handler
        self._events[(0, 4)].append((lambda packet: packet, lambda packet: self.stop()))
        # on stall handler
        self._events[(1, 29)].append((lambda packet: False, self.enable_motors))
        # on cliff handler
        self._events[(20, 0)].append(
            (
                lambda packet: packet.payload[4] == 0,
                self.enable_motors,
            )
        )
        self._inc = 0
        self._running = True

    def is_running(self) -> bool:
        """Return True if robot is running"""
        return self._running

    async def stop(self):
        """Stop robot and end communication"""
        await self.write_packet(Packet(0, 3, self.inc))
        self._running = False

    def enable_motors(self, enable: bool):
        """Block/allow motor commands"""
        self._enable_motors = enable

    def _data_received(self, data: bytes):
        if not self._running:
            return

        packet = Packet.from_bytes(data)
        debug(f"RX: {packet}")

        if not packet.check_crc():
            debug(f"CRC fail: {packet}")
            return

        key = (packet.dev, packet.cmd, packet.inc)
        if key in self._responses:
            future = self._responses.pop(key)
            if future and not future.done() and not future.cancelled():
                future.set_result(packet)

        key = (packet.dev, packet.cmd)
        if key in self._events:
            for (filter, callback) in self._events[key]:
                args = filter(packet)
                if args:
                    if key in self._tasks:
                        self._tasks[key].cancel()
                    self._tasks[key] = self._loop.create_task(callback(args))

    async def write_packet(self, packet: Packet):
        """Send a packet to robot"""
        if self._running:
            await self._bluetooth.write(packet.to_bytes())
            debug(f"TX: {packet}")
