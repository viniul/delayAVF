// This is free and unencumbered software released into the public domain.
//
// Anyone is free to copy, modify, publish, use, compile, sell, or
// distribute this software, either in source code form or as a compiled
// binary, for any purpose, commercial or non-commercial, and by any
// means.

#include "firmware.h"
#include "print.c"
#include "core_portme.h"
#include "ee_printf.c"

void main(void)
{ 
  while(1) {
    print_str("Hello Vincent!\n"); 
    print_dec(42);
    print_chr('\n');
    print_hex(0xDEAD,4);
    print_chr('\n');
    ee_printf("Vincent %x \n", 0xBEEF);
    ee_printf("Vincent %x %p \n", 0xBEEF, main);
    __asm__ volatile ("ebreak");
  }
}

