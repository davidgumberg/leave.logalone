The ugly bit here is that your pip install clang==x.x.x version should match as
closely as possible your system's `clang-devel` or `clang-dev` or `libclang-dev`
or w/e. Might not have the exact release, but there should be a matching
MAJOR.MINOR pip package for your clang library package

### LLM disclosure

I used LLM's heavily (in chat format) to build the first draft of this since a
great deal of the libclang python interface seems undocumented or expects
familiarity with the c interface.

I've reviewed every line of code in this repo and most of it has been rewritten
since the first draft.


