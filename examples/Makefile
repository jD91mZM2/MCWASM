.PHONY: all
all: \
	$(patsubst %.wat,build/%.wasm,$(wildcard *.wat)) \
	$(patsubst rust/%/Cargo.toml,build/rust/%.wasm,$(wildcard rust/*/Cargo.toml))

.PHONY: clean
clean:
	rm -rf build/
	cargo clean --manifest-path rust/Cargo.toml

build:
	[ -e $@ ] || mkdir $@
build/rust: build
	[ -e $@ ] || mkdir $@

build/%.wasm: %.wat build
	wat2wasm $< -o $@

rust/target/wasm32-unknown-unknown/release/%.wasm: rust/%/Cargo.* rust/%/src/*.rs
	cargo build --manifest-path rust/Cargo.toml --release --target wasm32-unknown-unknown
build/rust/%.wasm: rust/target/wasm32-unknown-unknown/release/%.wasm build/rust
	cp $< $@
