import js

DEBUG = False


def debug(string):
    if DEBUG:
        js.console.log(string)
