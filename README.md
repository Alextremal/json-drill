## json-drill


### Build
```sh
make plotter
```

### Usage
#### Run tests for Python module
```sh
python preprocessor/tests/main.py
```
#### Run the main program
```sh
./build/plotter [dataset]
```
Example:
```sh
./build/plotter ../spec/datasets/01_small.json
```

### Requirements
- Python 3.11+
- GCC or Clang
- GNU Make
- Raylib
