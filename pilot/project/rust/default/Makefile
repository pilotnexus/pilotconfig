release: prepare
	cargo build --release && cp target/thumbv7m-none-eabi/release/libpilot.a lib/
	cd basefw/stm && make rust && cp stm.bin ../../out

debug: prepare
	cargo build && cp target/thumbv7m-none-eabi/release/libpilot.a lib/
	cd basefw/stm && make rust && cp stm.bin ../../out

prepare:
	mkdir -p out
	mkdir -p lib
	rm -f target/thumbv7m-none-eabi/release/stm
clean:
	cd basefw/stm && make clean
	rm -f lib/*
	cargo clean
