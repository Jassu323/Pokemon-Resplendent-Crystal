#include "Core/gb.h"
#include <stdio.h>
static GB_gameboy_t gb;
int main(int argc,char **argv) {
 GB_init(&gb,GB_MODEL_CGB_E);
 if(argc!=3 || GB_load_rom(&gb,argv[1]) || GB_load_state(&gb,argv[2])) return 1;
 unsigned hits=0;
 for(unsigned n=0;n<2000000 && hits<12;n++) {
  if(gb.pc==0x14b2 || gb.pc==0x14be || gb.pc==0x02f1 || gb.pc==0x14c0) {
   printf("pc=%04x ly=%u phase=%u af=%04x size=%u tick=%u\n",gb.pc,gb.io_registers[0x44],gb.display_cycles,gb.af,gb.hram[0x53],gb.hram[0x1b]);
   if(gb.pc==0x14b2) hits++;
  }
  GB_run(&gb);
 }
 GB_free(&gb);
}
