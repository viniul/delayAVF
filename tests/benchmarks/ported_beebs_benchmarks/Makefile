TOOLCHAIN_PREFIX ?= riscv64-zephyr-elf-

%.elf: %.c ../minimal_firmware/start_serv.S ../minimal_firmware/link.ld
	$(TOOLCHAIN_PREFIX)gcc -I../../minimal_firmware -specs=picolibc.specs -ffreestanding -nostartfiles -nostdlib -march=rv32i -mabi=ilp32 -T../minimal_firmware/link.ld ../minimal_firmware/start_serv.S -O3 -o$@ $< main.c ../minimal_firmware/util.c
%.bin: %.elf
	$(TOOLCHAIN_PREFIX)objcopy -O binary $< $@
%.hex: %.bin
	python3 ../minimal_firmware/makehex.py $< > $@

clean:
	rm -f *.elf *.bin *.hex


