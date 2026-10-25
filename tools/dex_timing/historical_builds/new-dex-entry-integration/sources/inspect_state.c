#include "Core/gb.h"
#include <stdio.h>
static GB_gameboy_t gb;
int main(int argc,char**argv) {
 GB_init(&gb,GB_MODEL_CGB_E);
 if(argc!=3 || GB_load_rom(&gb,argv[1]) || GB_load_state(&gb,argv[2])) return 1;
 printf("pc %04x bank %x sp %04x af %04x bc %04x de %04x hl %04x\n",gb.pc,gb.mbc_rom_bank,gb.sp,gb.af,gb.bc,gb.de,gb.hl);
 for(unsigned a=gb.sp;a<0xc100;a++) printf("%04x=%02x ",a,gb.ram[a&4095]);
 puts("\nHRAM");for(unsigned a=0;a<127;a++) printf("%04x=%02x ",0xff80+a,gb.hram[a]);
 puts("\nIO");for(unsigned a=0;a<128;a++) printf("%04x=%02x ",0xff00+a,gb.io_registers[a]);
 puts("");GB_free(&gb);
}
