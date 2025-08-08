# EOT tools

Tools for working with EOT (Embedded OpenType) font files.

## About

Embedded OpenType (EOT) fonts are a font format mostly used in Microsoft applications. The primary
usage has been as a webfont in Internet Explorer. Nowadays, it is mostly unused, but when dealing
with legacy distributions, we might need a deeper look into their properties. Additionally, tools
like [Fontello](https://github.com/fontello/fontello) still generate EOT font files by default. 

When looking for FOSS tooling around EOT fonts, I could not find any reliable parser that would
allow further inspection of these files. With the specification being [publicly available](https://www.w3.org/submissions/EOT/)
and the files basically being a TTF file with some header/prefix, basic processing is rather
straightforward. Thus, I decided to write a short script for it to later move it into a library
to make metadata/property analysis of EOT possible.

The corresponding TTF files can be analyzed with a much wider variety of tools, for example,
using the [fonttools](https://github.com/fonttools/fonttools) library.

## Features

* Read all defined properties.
* Retrieve the embedded TTF file data. Currently limited to uncompressed and unencrypted data as this
  is what the test files I found use.

## Installation

You can install this package from PyPI:

```bash
python -m pip install eot_tools
```

Alternatively, you can use the package from source directly after installing the required dependencies.

## Usage

To load an EOT file, use the following code:

```python
from eot_tools import EOTFile


eot = EOTFile("Maki.eot")
print(eot.family_name, eot.style_name, eot.version_name)
```

Once the file is loaded, you can use `fonttools` to load the actual font for example:

```python
from io import BytesIO

from eot_tools import EOTFile
from fontTools.ttLib import TTFont


eot = EOTFile("Maki.eot")
with TTFont(file=BytesIO(eot.font_data)) as font:
    print(font)
```

## License

This package is subject to the terms of the MIT license.
