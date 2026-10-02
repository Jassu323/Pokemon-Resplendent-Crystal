#include "Core/gb.h"
#include <stdio.h>
#include <stdlib.h>

/* Host-only reference probe. Does not load a game, save, or save state. */
int main(void)
{
    GB_gameboy_t *gb = calloc(1, sizeof(*gb));
    GB_init(gb, GB_MODEL_CGB_E);
    gb->cgb_mode = true;
    gb->disable_rendering = true;
    GB_write_memory(gb, 0xff40, 0);
    for (unsigned blocks = 1; blocks <= 14; blocks += 13) {
        GB_write_memory(gb, 0xff51, 0xc0);
        GB_write_memory(gb, 0xff52, 0);
        GB_write_memory(gb, 0xff53, 0);
        GB_write_memory(gb, 0xff54, 0);
        GB_write_memory(gb, 0xff55, blocks - 1);
        unsigned before = gb->cycles_since_run;
        GB_hdma_run(gb);
        printf("dma blocks=%u T=%u\n", blocks, (gb->cycles_since_run - before) / 2);
    }
    GB_write_memory(gb, 0xff43, 5);
    GB_write_memory(gb, 0xff4a, 0);
    GB_write_memory(gb, 0xff4b, 167);
    GB_write_memory(gb, 0xff41, 8);
    GB_write_memory(gb, 0xff40, 0xe3);
    unsigned origin = 0, frames = 0, old_ly = 255, old_mode = 255;
    for (unsigned t = 1; t < 5 * 70224; t++) {
        GB_advance_cycles(gb, 1);
        unsigned ly = GB_read_memory(gb, 0xff44);
        unsigned mode = GB_read_memory(gb, 0xff41) & 3;
        unsigned flags = GB_read_memory(gb, 0xff0f) & 3;
        if (flags & 1) {
            origin = t;
            frames++;
        }
        if (frames == 3 && (ly != old_ly || mode != old_mode || flags)) {
            printf("t=%u offset=%u ly=%u mode=%u if=%u\n", t, t-origin, ly, mode, flags);
        }
        if (frames == 3 && gb->current_line == 145 &&
            gb->display_state == 13 && -gb->display_cycles / 2 == 300) {
            printf("luxray_publication_lcd offset=%u line=%u state=%u sleep=%d\n",
                   t-origin, gb->current_line, gb->display_state, -gb->display_cycles / 2);
        }
        old_ly = ly;
        old_mode = mode;
        gb->io_registers[GB_IO_IF] = 0;
    }
    GB_free(gb);
    free(gb);
    return 0;
}
