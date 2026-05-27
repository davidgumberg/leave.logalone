## Setup

```bash
python -m venv .venv
pip install clang # read below...
```

The ugly bit here is that in some cases I've run into issues when the python
`clang` package and your system's `clang-devel` or `clang-dev` or `libclang-dev`
or w/e are too far apart. If you run into strange issues it may be worth trying
to match `pip install clang==x.x.x` as closely as possible to your system's
package.

## Usage

This is intended to be used as a library in the future but also supports being
run as a script, mainly since this has been helpful for me while iterating.

```bash
python leave/logalone.py /Path/To/BitcoinCore strings.json
```

### LLM disclosure

I used LLM's heavily to build the first draft of the part of this code that
interacts with libclang since much of the libclang python interface seems
undocumented or expects familiarity with the c interface.

Every line of code in here, unless indicated otherwise, has been read and
understood by me.
