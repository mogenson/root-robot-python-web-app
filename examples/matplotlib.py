# we can access Javascript and modify the HTML document from Python
import asyncio
import base64
import io

import js

await js.pyodide.loadPackage("matplotlib")
import matplotlib.pyplot as plt

data = []
await robot.reset_position()
await robot.set_speeds(10, 10)
for i in range(0, 20):
    position = await robot.get_position()
    data.append(position[1])
    await asyncio.sleep(0.05)
await robot.set_speeds(0, 0)

fig, ax = plt.subplots()
ax.plot(data)
img = js.document.createElement("img")
js.document.body.appendChild(img)
png = io.BytesIO()
fig.savefig(png, format="png")
img.src = "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()
