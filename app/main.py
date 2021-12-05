import asyncio
import sys

import js
import pyodide

from .bluetooth import Bluetooth
from .debug import debug
from .output import OutputIO
from .robot import *


class App:
    def __init__(self):
        self.output = OutputIO()
        sys.stdout = self.output
        self.editor = js.editor
        self.loop = asyncio.get_running_loop()
        self.bluetooth = Bluetooth()
        self.bluetooth.disconnected_callback = self.disconnected
        self.robot = Robot(self.bluetooth)
        self.play_button = js.document.getElementById("play")
        self.play_button.onclick = lambda event: self.loop.create_task(self.play())
        self.connect_button = js.document.getElementById("connect")
        self.connect_button.onclick = lambda event: self.loop.create_task(
            self.connect()
        )
        self.connect_button.disabled = False
        self.open_button = js.document.getElementById("open")
        self.open_button.onclick = lambda event: self.loop.create_task(self.open())
        self.save_button = js.document.getElementById("save")
        self.save_button.onclick = lambda event: self.loop.create_task(self.save())
        self.user_program = None
        self.file_handle = None
        self.file_options = {"types": [{"accept": {"text/python": [".py"]}}]}
        self.file_options = pyodide.to_js(
            self.file_options, dict_converter=js.Object.fromEntries
        )
        self.set_examples()

    def disconnected(self):
        self.connect_button.innerHTML = "Connect"
        self.connect_button.disabled = False
        self.play_button.disabled = True
        debug("disconnected")
        self.output.notify("Disconnected")

    async def connect(self):
        if not self.bluetooth.is_connected():
            debug("connect")
            self.connect_button.disabled = True
            await self.bluetooth.connect()
            self.connect_button.innerHTML = "Disconnect"
            self.connect_button.disabled = False
            self.play_button.disabled = False
            debug("connected")
            self.output.notify("Connected")
        else:
            debug("disconnect")
            self.connect_button.disabled = True
            self.bluetooth.disconnect()

    async def play(self):
        if not self.robot.is_running():
            self.play_button.innerHTML = "Stop"
            self.output.clear()
            await self.robot.run()
            code = self.editor.getValue()
            exec(
                "async def _user_program(robot):"
                + "".join(f"\n {line}" for line in code.split("\n"))
            )
            self.user_program = self.loop.create_task(
                locals()["_user_program"](self.robot)
            )
        else:
            self.user_program.cancel()
            await self.robot.stop()
            self.play_button.innerHTML = "Play"

    async def open(self):
        file_handles = await js.window.showOpenFilePicker(self.file_options)
        self.file_handle = file_handles[0]
        blob = await self.file_handle.getFile()
        text = await blob.text()
        self.editor.setValue(text, -1)
        self.output.notify(f"Opened {self.file_handle.name}")

    async def save(self):
        if not self.file_handle:
            self.file_handle = await js.window.showSaveFilePicker(self.file_options)
        writable = await self.file_handle.createWritable()
        await writable.write(self.editor.getValue())
        await writable.close()
        self.output.notify(f"Saved {self.file_handle.name}")

    def set_examples(self):
        def _set_example(id):
            with open(sys.path[-1] + "/examples/" + id + ".py") as example:
                self.editor.setValue(example.read(), -1)

        for example in ["events", "matplotlib", "micropip"]:
            js.document.getElementById(
                example
            ).onclick = lambda event, example=example: _set_example(example)


async def main():
    app = App()
