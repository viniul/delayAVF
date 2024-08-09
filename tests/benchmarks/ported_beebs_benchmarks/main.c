#include "firmware.h"
#include "print.c"

void initialise_benchmark(void);
int benchmark(void);
int verify_benchmark (int);

void main(void){
     initialise_benchmark();
     int res = benchmark();
     verify_benchmark(res);
      __asm__ volatile ("wfi");
     __asm__ volatile ("ebreak");
     return;
}

