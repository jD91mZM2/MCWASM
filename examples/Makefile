.PHONY: all
all: $(patsubst %.wat,build/%.wasm,$(wildcard *.wat))

.PHONY: clean
clean:
	rm -rf build/*.wasm

build/%.wasm: %.wat
	wat2wasm $< -o $@
