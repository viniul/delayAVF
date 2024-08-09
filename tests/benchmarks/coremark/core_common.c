#include "core_portme.h"
#include "coremark.h"
#include "firmware.h"
#include "ee_printf.c"

static ee_u16 list_known_crc[]   = { (ee_u16)0xd4b0,
                                   (ee_u16)0x3340,
                                   (ee_u16)0x6a79,
                                   (ee_u16)0xe714,
                                   (ee_u16)0xe3c1 };
static ee_u16 matrix_known_crc[] = { (ee_u16)0xbe52,
                                     (ee_u16)0x1199,
                                     (ee_u16)0x5608,
                                     (ee_u16)0x1fd7,
                                     (ee_u16)0x0747 };
static ee_u16 state_known_crc[]  = { (ee_u16)0x5e47,
                                    (ee_u16)0x39bf,
                                    (ee_u16)0xe5a4,
                                    (ee_u16)0x8e3a,
                                    (ee_u16)0x8d84 };

#if (MEM_METHOD == MEM_STATIC)
ee_u8 static_memblk[TOTAL_DATA_SIZE];
#endif
