#include "firmware.h"
#include "print.c"
#include <stdio.h>
#include <math.h>

#define HASH_SIZE   (1 << 16)//(1 << 16)
#define HASH(h, x)  (h = (h << 4) ^ x) //(h = (h << 4) ^ x)
#define MAX_RLEN 50

void encode(unsigned char *input, unsigned int inputlen, unsigned char *output, unsigned int *outlen) {
    //print_chr('E');
    //print_chr('\n');
    unsigned char buf[9], table[HASH_SIZE]; //= {0};
    unsigned short hash = 0;
    int mask, i, j, c, inpos = 0, outpos = 0;
    
    for (;;) {
        //print_chr('A');
        //print_chr('\n');
        j = 1;
        mask = 0;
        for (i = 0; i < 8; i++) {
            //print_chr('A');
            //print_chr('\n');
            if (inpos == inputlen) break;
            c = input[inpos++];
            if (c == table[hash]) {
                mask |= 1 << i;
            } else {
                table[hash] = c;
                buf[j++] = c;
            }
            HASH(hash, c);
        }
        if (i > 0) {
            buf[0] = mask;
            for (i=0;i<j;i++) { output[outpos++] = buf[i]; } // one-liner copy function
        }
        if (inpos == inputlen) break;
    }
    *outlen = outpos;
}

void decode(unsigned char *input, unsigned int inputlen, unsigned char *output, unsigned int *outlen) {
    unsigned char buf[8], table[HASH_SIZE];// = {0};
    unsigned short hash = 0;
    int mask, i, j, c, inpos = 0, outpos = 0;
    
    for (;;) {
        j = 0;
        if (inpos == inputlen) break;
        mask = input[inpos++];
        for (i = 0; i < 8; i++) {
            if ((mask & (1 << i)) != 0) {
                c = table[hash];
            } else {
                if (inpos == inputlen) break;
                c = input[inpos++];
                table[hash] = c;
            }
            buf[j++] = c;
            HASH(hash, c);
        }
        if (j > 0) {
            for (i=0;i<j;i++) { output[outpos++] = buf[i]; } // one-liner copy function
        }
    }
    *outlen = outpos;
}


/* Returns the Run Length Encoded string for the 
   source string src */
void encode_rle(char* src,  int inputlen, char *dest)
{
    int rLen;
    char count[MAX_RLEN];
    int len = inputlen;
 
 
    int i, j = 0, k;
 
    /* traverse the input string one by one */
    for (i = 0; i < len; i++) {
 
        /* Copy the first occurrence of the new character */
        //dest[j++] = src[i];
        print_chr(src[i]);
 
        /* Count the number of occurrences of the new character */
        rLen = 1;
        while (i + 1 < len && src[i] == src[i + 1]) {
            rLen++;
            i++;
        }
 
        /* Store rLen in a character array count[] */
        //sprintf(count, "%d", rLen);
        print_dec(rLen);
        /* Copy the count[] to destination */
        for (k = 0; *(count + k); k++, j++) {
            //dest[j] = count[k];
            //print_dec(count[k]);
        }
    }
 
    /*terminate the destination string */
    dest[j] = '\0';
    return dest;
}

void main(void)
{
  unsigned int strlen = 7, outlen;
  unsigned char str[1024] = "Superlongcomplicatedstring";
  unsigned char out[1024];
  /* If all characters in the source string are different, 
    then size of destination string would be twice of input string.
    For example if the src is "abcd", then dest would be "a1b1c1d1"
    For other inputs, size would be less than twice.  */
 //char dest[strlen*2+1];//= (char*)malloc(sizeof(char) * (len * 2 + 1));
 
  //print_chr('A');
  //print_chr('\n');
  encode(str, strlen, out, &outlen);
  decode(out, outlen, str, &outlen);
 
  //print_chr('A');
//  while(1) {
    //encode_rle(str, strlen, out);
    //print_chr('A');
    //print_chr('\n');
    //ciphertext[16] = NULL;
    print_str(str);
    //print_chr('\n');
    print_chr('\n');
    __asm__ volatile ("ebreak"); 
    //AES_encrypt(ciphertext);
    //print_hex_str(ciphertext);
    //print_chr('\n');
  //}
}
