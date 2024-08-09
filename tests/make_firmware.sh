#!/bin/bash
set -e
#set -x
TOOLCHAIN_PREFIX=riscv64-unknown-elf-
if [ -f "/root/zephyr-sdk-0.16.1/riscv64-zephyr-elf/bin/riscv64-zephyr-elf-gcc" ]; then
   TOOLCHAIN_PREFIX="/root/zephyr-sdk-0.16.1/riscv64-zephyr-elf/bin/riscv64-zephyr-elf-"
   echo "Setting $TOOLCHAIN_PREFIX"
fi
export TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX
# Build benchmarks
cd benchmarks/hello_vincent
TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make hello_vincent.hex
#make hello_vincent.hex
cd ../mat_mult/
rm -rf mat_mult.hex
TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make mat_mult.hex
cd ../mat_mult_large/
rm -rf mat_mult_large.hex
TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make mat_mult_large.hex
#make mat_mult.hex
cd ../aes_encryption
rm -rf aes_encrypt.hex
TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make aes_encrypt.hex
#make aes_encrypt.hex
cd ../lzp
rm -rf lzp.hex
TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make lzp.hex
cd ../ported_beebs_benchmarks
benchmarks=("md5.hex" "libcrc.hex" "libbubblesort.hex" "libstrstr.hex" "matmult.hex" "libfibcall.hex" "liblevenshtein.hex")
for file in "${benchmarks[@]}"; do
    
    rm -f "$file" # -f to not fail if file does not exist
    echo "Now making $file beebs benchmark"
    TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX make $file
done
#make aes_encrypt.hex
cd ../../
