#define PROGRAM_NAME "pokemon_animation"
#define USAGE_OPTS "[-h|--help] [-b|--bitmasks] [-f|--frames] [-d|--dex-plan file] front.animated.tilemap front.dimensions"

#include "common.h"

struct Options {
	bool use_bitmasks;
	bool use_frames;
	const char *dex_plan_filename;
};

void parse_args(int argc, char *argv[], struct Options *options) {
	struct option long_options[] = {
		{"bitmasks", no_argument, 0, 'b'},
		{"frames", no_argument, 0, 'f'},
		{"dex-plan", required_argument, 0, 'd'},
		{"help", no_argument, 0, 'h'},
		{0}
	};
	for (int opt; (opt = getopt_long(argc, argv, "bfd:h", long_options)) != -1;) {
		switch (opt) {
		case 'b':
			options->use_bitmasks = true;
			break;
		case 'f':
			options->use_frames = true;
			break;
		case 'd':
			options->dex_plan_filename = optarg;
			break;
		case 'h':
			usage_exit(0);
			break;
		default:
			usage_exit(1);
		}
	}
}

struct DexPlanTile {
	uint8_t position;
	uint8_t source;
};

static int compare_dex_plan_tiles(const void *left, const void *right) {
	const struct DexPlanTile *a = left;
	const struct DexPlanTile *b = right;
	bool a_uses_base = a->position & 0x80;
	bool b_uses_base = b->position & 0x80;
	if (a_uses_base != b_uses_base) {
		return b_uses_base - a_uses_base;
	}
	if (a->source != b->source) {
		return a->source - b->source;
	}
	return a->position - b->position;
}

static int make_dex_plan_tiles(const uint8_t *base, const uint8_t *frame,
		int width, struct DexPlanTile *tiles) {
	int row_offset = width == 5 ? 2 : width == 6 ? 1 : 0;
	int col_offset = width == 7 ? 0 : 1;
	int count = 0;

	// Animation tilemaps are column-major. Store explicit row-major positions
	// so the runtime does not need to expand bitmasks or calculate coordinates.
	for (int col = 0; col < width; col++) {
		for (int row = 0; row < width; row++) {
			int index = col * width + row;
			if (frame[index] == base[index]) {
				continue;
			}
			tiles[count].position = (row + row_offset) * 7 + col + col_offset;
			tiles[count].source = frame[index];
			if (frame[index] < width * width) {
				int source_col = frame[index] / width;
				int source_row = frame[index] % width;
				tiles[count].position |= 0x80;
				tiles[count].source =
					(source_col + col_offset) * 7 + source_row + row_offset;
			}
			count++;
		}
	}

	// Dictionary tiles arrive in ascending order. Keeping each plan in that
	// order lets the existing producer upload every ready prefix immediately.
	qsort(tiles, count, sizeof *tiles, compare_dex_plan_tiles);
	return count;
}

static void write_dex_plan(const char *filename, const uint8_t *tilemap,
		long tilemap_size, int width) {
	int frame_size = width * width;
	int num_frames = tilemap_size / frame_size - 1;
	struct DexPlanTile tiles[7 * 7];
	size_t output_size = num_frames * 2;

	for (int i = 0; i < num_frames; i++) {
		const uint8_t *frame = tilemap + (i + 1) * frame_size;
		int count = make_dex_plan_tiles(tilemap, frame, width, tiles);
		output_size += 1 + count * 2;
	}
	if (output_size > UINT16_MAX) {
		error_exit("%s: Dex animation plan is too large\n", filename);
	}

	uint8_t *output = xmalloc(output_size);
	size_t offset = num_frames * 2;
	for (int i = 0; i < num_frames; i++) {
		const uint8_t *frame = tilemap + (i + 1) * frame_size;
		int count = make_dex_plan_tiles(tilemap, frame, width, tiles);
		output[i * 2] = offset & 0xff;
		output[i * 2 + 1] = offset >> 8;
		output[offset++] = count;
		for (int j = 0; j < count; j++) {
			output[offset++] = tiles[j].position;
			output[offset++] = tiles[j].source;
		}
	}

	write_u8(filename, output, output_size);
	free(output);
}

struct Frame {
	uint8_t *data;
	int size;
	int bitmask;
};

struct Frames {
	struct Frame *frames;
	int num_frames;
};

struct Bitmask {
	uint8_t *data;
	int bitlength;
};

struct Bitmasks {
	struct Bitmask *bitmasks;
	int num_bitmasks;
};

int bitmask_exists(const struct Bitmask *bitmask, const struct Bitmasks *bitmasks) {
	for (int i = 0; i < bitmasks->num_bitmasks; i++) {
		struct Bitmask existing = bitmasks->bitmasks[i];
		if (bitmask->bitlength != existing.bitlength) {
			continue;
		}
		bool match = true;
		int length = (bitmask->bitlength + 7) / 8;
		for (int j = 0; j < length; j++) {
			if (bitmask->data[j] != existing.data[j]) {
				match = false;
				break;
			}
		}
		if (match) {
			return i;
		}
	}
	return -1;
}

void make_frames(const uint8_t *tilemap, long tilemap_size, int width, struct Frames *frames, struct Bitmasks *bitmasks) {
	int num_tiles_per_frame = width * width;
	int num_frames = tilemap_size / num_tiles_per_frame - 1;

	frames->frames = xmalloc((sizeof *frames->frames) * num_frames);
	frames->num_frames = num_frames;

	bitmasks->bitmasks = xmalloc((sizeof *bitmasks->bitmasks) * num_frames);
	bitmasks->num_bitmasks = 0;

	const uint8_t *first_frame = &tilemap[0];
	const uint8_t *this_frame = &tilemap[num_tiles_per_frame];
	for (int i = 0; i < num_frames; i++) {
		struct Frame *frame = xmalloc(sizeof *frame);
		frame->data = xmalloc(num_tiles_per_frame);
		frame->size = 0;

		struct Bitmask *bitmask = xmalloc(sizeof *bitmask);
		bitmask->data = xcalloc((num_tiles_per_frame + 7) / 8);
		bitmask->bitlength = 0;

		for (int j = 0; j < num_tiles_per_frame; j++) {
			if (bitmask->bitlength % 8 == 0) {
				bitmask->data[bitmask->bitlength / 8] = 0;
			}
			bitmask->data[bitmask->bitlength / 8] >>= 1;
			if (this_frame[j] != first_frame[j]) {
				frame->data[frame->size] = this_frame[j];
				frame->size++;
				bitmask->data[bitmask->bitlength / 8] |= (1 << 7);
			}
			bitmask->bitlength++;
		}
		// tile order ABCDEFGHIJKLMNOP... becomes db order %HGFEDCBA %PONMLKJI ...
		int last = bitmask->bitlength - 1;
		bitmask->data[last / 8] >>= (7 - (last % 8));

		frame->bitmask = bitmask_exists(bitmask, bitmasks);
		if (frame->bitmask == -1) {
			frame->bitmask = bitmasks->num_bitmasks;
			bitmasks->bitmasks[bitmasks->num_bitmasks] = *bitmask;
			bitmasks->num_bitmasks++;
		} else {
			free(bitmask->data);
			free(bitmask);
		}
		frames->frames[i] = *frame;
		this_frame += num_tiles_per_frame;
	}
}

void print_frames(struct Frames *frames) {
	for (int i = 0; i < frames->num_frames; i++) {
		printf("\tdw .frame%d\n", i + 1);
	}
	for (int i = 0; i < frames->num_frames; i++) {
		const struct Frame *frame = &frames->frames[i];
		printf(".frame%d\n", i + 1);
		printf("\tdb $%02x ; bitmask\n", frame->bitmask);
		if (frame->size > 0) {
			for (int j = 0; j < frame->size; j++) {
				if (j % 12 == 0) {
					if (j) {
						putchar('\n');
					}
					printf("\tdb $%02x", frame->data[j]);
				} else {
					printf(", $%02x", frame->data[j]);
				}
			}
			putchar('\n');
		}
	}
}

void print_bitmasks(const struct Bitmasks *bitmasks) {
	for (int i = 0; i < bitmasks->num_bitmasks; i++) {
		struct Bitmask bitmask = bitmasks->bitmasks[i];
		printf("; %d\n", i);
		int length = (bitmask.bitlength + 7) / 8;
		for (int j = 0; j < length; j++) {
			printf("\tdb %%");
			for (int k = 0; k < 8; k++) {
				putchar(((bitmask.data[j] >> (7 - k)) & 1) ? '1' : '0');
			}
			putchar('\n');
		}
	}
}

int main(int argc, char *argv[]) {
	struct Options options = {0};
	parse_args(argc, argv, &options);

	argc -= optind;
	argv += optind;
	if (argc < 2) {
		usage_exit(1);
	}

	int width;
	read_dimensions(argv[1], &width);
	long tilemap_size;
	uint8_t *tilemap = read_u8(argv[0], &tilemap_size);

	struct Frames frames = {0};
	struct Bitmasks bitmasks = {0};
	make_frames(tilemap, tilemap_size, width, &frames, &bitmasks);

	if (options.use_frames) {
		print_frames(&frames);
	}
	if (options.use_bitmasks) {
		print_bitmasks(&bitmasks);
	}
	if (options.dex_plan_filename) {
		write_dex_plan(options.dex_plan_filename, tilemap, tilemap_size, width);
	}

	free(tilemap);
	return 0;
}
