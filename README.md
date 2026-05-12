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

I used LLM's heavily to build the first draft of this since a great deal of the
libclang python interface seems undocumented or expects familiarity with the c
interface.

I've since reviewed every line of code in this repo and most of it has been
rewritten since the first draft.


