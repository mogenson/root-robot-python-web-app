# Root Robot Python Web App

An online Python code editor. Control an iRobot Root Robot over Bluetooth with
Python.

Hosted at: https://root-robot-python.web.app

Made with [Pyodide](https://pyodide.org) and [Ace](https://ace.c9.io) editor.
Python sources are compiled to bytecode, compressed, extracted to the browser's
virtual file system, then run with a web assembly Python interpreter.

Uses the [Web Bluetooth](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
and [File System Access](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)
browser APIs. These require a Chrome browser.

## Build

Requirements: `Python 3.9`, `bash`, `make`, `zip`, and `find`.

```
$ make build
```

Static site assets will be in the `public` directory.

## Run

```
$ make run
```

Navigate to `http://localhost:8000` in Chrome browser.

## Clean

```
$ make clean
```

## Format and lint code

Requirements: `isort`, `black`, and `pylint`.

```
$ make lint
```

-------------------------------------------------------------------------------

"Root Robot" is a trademark of iRobot Corporation. This is not an iRobot
product.
