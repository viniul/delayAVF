#include "firmware.h"
#include "print.c"
#include <stdio.h>
#include <math.h>

/*
void do_fp_op(){
    double x = 0.0;
    double y = 2.0;
    double result = x+y;
    double logresult = log10(100);
    char out[200];
    out[0] = '\0';
    out[1] = 'V';
    int8_t x_int = 42;

    sprintf(out, "res %llx \n", result);// = %f\n", result);// result
    sprintf(out, "logres %llx \n", logresult);// = %f\n", result);// result
}
*/


void main(void)
{

    //do_fp_op();
    volatile int a[9] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
    volatile int b[9] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
    volatile int c[9] = {0};

    int n = 3;
    
    for (int i = 0; i < 9; i++) {
      uint8_t result = c[i];
    }
    
    for (int i = 0; i < n; i++) {
      for (int j = 0; j < n; j++) {
        *(c + i * n + j) = 0;
        for (int k = 0; k < n; k++) {
          *(c + i * n + j) = *(c + i * n + j) + *(a + i * n + k) * *(b + k * n + j);
        }
      }
    } 

    int sum = 0;

    for (int i = 0; i < 9; i++) {
      sum += c[i];
    }
    print_dec(sum);
    print_chr('\n');

 __asm__ volatile ("ebreak"); 

}
