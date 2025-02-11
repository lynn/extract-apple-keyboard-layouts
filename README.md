# extract-apple-keyboard-layouts
Python script for parsing and converting the default Mac keyboard layouts file at `/System/Library/Keyboard Layouts/AppleKeyboardLayouts.bundle/Contents/Resources/AppleKeyboardLayouts-L.dat`.

Usage: `python3 extract.py` (there are no dependencies, you'll just need Python 3.8+).

References:

* ["Format of AppleKeyboardLayouts-L.dat" on the ukelele-users group](https://groups.google.com/g/ukelele-users/c/xRo9BwPeFpg)
* [uchr specification](https://leopard-adc.pepas.com/documentation/Carbon/Reference/Unicode_Utilities_Ref/uu_app_uchr/uu_app_uchr.html)

For now it just parses the file and checks that I can play with the contents of `Dvorak`. The idea is to convert them from binary to XML `.keylayout` files that can be easily edited (by hand or with [Ukelele](https://software.sil.org/ukelele/)) and added to `~/Library/Keyboard Layouts`.
