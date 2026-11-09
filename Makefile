BUILD=./build

.PHONY: plotter

plotter: $(BUILD)/plotter
$(BUILD)/plotter: plotter/plotter.c | $(BUILD)
	cc plotter/plotter.c -o $(BUILD)/plotter -lraylib

$(BUILD):
	mkdir -p $(BUILD)
