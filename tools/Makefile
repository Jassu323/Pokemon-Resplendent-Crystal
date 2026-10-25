.PHONY: all clean

CC := gcc
CFLAGS := -O3 -flto -std=c11 -Wall -Wextra -pedantic

tools := \
	gbcpal \
	frontpic_lz \
	gfx \
	lzcomp \
	make_patch \
	png_dimensions \
	pokemon_animation \
	pokemon_animation_graphics \
	scan_includes

all: $(tools)
	@:

clean:
	$(RM) $(tools)

lzcomp: CFLAGS += -Wno-strict-overflow -Wno-sign-compare
lzcomp: $(wildcard lz/*.c) $(wildcard lz/*.h)
	$(CC) $(CFLAGS) -o $@ lz/*.c

frontpic_lz_sources := frontpic_lz.c $(filter-out lz/main.c lz/options.c lz/uncomp.c,$(wildcard lz/*.c))
frontpic_lz: CFLAGS += -Wno-strict-overflow -Wno-sign-compare
frontpic_lz: $(frontpic_lz_sources) $(wildcard lz/*.h)
	$(CC) $(CFLAGS) -o $@ $(frontpic_lz_sources)

%: %.c common.h
	$(CC) $(CFLAGS) -o $@ $<
