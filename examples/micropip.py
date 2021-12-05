# import micropip package manager
import micropip

# install art package from PyPI
await micropip.install("art")

# can also specify full URL to wheel
# await micropip.install("https://files.pythonhosted.org/packages/b5/7c/c97aba89a6c50766becfcc715edcae3ac6f78b90548a4efcb73f6901adee/art-5.3-py2.py3-none-any.whl")

# import and use package
import art

print(art.text2art("Hello World"))
