#include "firmware.h"
#include "print.c"
#include <stdio.h>
#include <math.h>
#include "aes.h"


void main(void)
{
  unsigned char ciphertext[17];
  ciphertext[0] = 0x64;
  ciphertext[1] = '\0';
  //print_chr('A');
  while(1) {
    //print_chr('A');
    //print_chr('\n');
    ciphertext[16] = NULL;
    print_hex_str(ciphertext);
    //print_chr('\n');
    print_chr('\n');
    AES_encrypt(ciphertext);
    print_hex_str(ciphertext);
    print_chr('\n');
  }
}
