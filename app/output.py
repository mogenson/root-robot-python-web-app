import io

import js


class OutputIO(io.TextIOBase):
    def __init__(self):
        super().__init__()
        self.output = js.document.getElementById("output")

    def write(self, string):
        self.output.innerHTML += string

    def clear(self):
        self.output.innerHTML = ""

    def notify(self, string):
        self.clear()
        self.write(string)
