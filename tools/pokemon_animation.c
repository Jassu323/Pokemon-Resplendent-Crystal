#define PROGRAM_NAME "pokemon_animation"
#define USAGE_OPTS "[-h|--help] [-b|--bitmasks] [-f|--frames] [-d|--dex-plan file] [--dex-timeline file] front.animated.tilemap front.dimensions [anim.asm anim_idle.asm]"

#include "common.h"
#include <ctype.h>

struct Options {
	bool use_bitmasks;
	bool use_frames;
	const char *dex_plan_filename;
	const char *dex_timeline_filename;
};

void parse_args(int argc, char *argv[], struct Options *options) {
	struct option long_options[] = {
		{"bitmasks", no_argument, 0, 'b'},
		{"frames", no_argument, 0, 'f'},
		{"dex-plan", required_argument, 0, 'd'},
		{"dex-timeline", required_argument, 0, 't'},
		{"help", no_argument, 0, 'h'},
		{0}
	};
	for (int opt; (opt = getopt_long(argc, argv, "bfd:t:h", long_options)) != -1;) {
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
		case 't':
			options->dex_timeline_filename = optarg;
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
		output_size += 2 + count * 2;
	}
	if (output_size > UINT16_MAX) {
		error_exit("%s: Dex animation plan is too large\n", filename);
	}

	uint8_t *output = xmalloc(output_size);
	size_t offset = num_frames * 2;
	for (int i = 0; i < num_frames; i++) {
		const uint8_t *frame = tilemap + (i + 1) * frame_size;
		int count = make_dex_plan_tiles(tilemap, frame, width, tiles);
		int high_water = width * width;
		output[i * 2] = offset & 0xff;
		output[i * 2 + 1] = offset >> 8;
		output[offset++] = count;
		for (int j = 0; j < count; j++) {
			if (!(tiles[j].position & 0x80) && tiles[j].source + 1 > high_water) {
				high_water = tiles[j].source + 1;
			}
		}
		output[offset++] = high_water;
		for (int j = 0; j < count; j++) {
			output[offset++] = tiles[j].position;
			output[offset++] = tiles[j].source;
		}
	}

	write_u8(filename, output, output_size);
	free(output);
}

enum AnimCommandType {
	ANIM_FRAME,
	ANIM_SETREPEAT,
	ANIM_DOREPEAT,
	ANIM_END,
};

struct AnimCommand {
	enum AnimCommandType type;
	int first;
	int second;
	int line;
};

struct AnimScript {
	struct AnimCommand *commands;
	int count;
	int capacity;
	const char *filename;
};

struct TimelineEvent {
	uint8_t frame;
	uint8_t duration;
	uint8_t target;
};

struct Timeline {
	struct TimelineEvent *events;
	int count;
	int capacity;
	int loop_start;
};

enum {
	DEX_DICTIONARY_CHUNK_TILES = 6,
	DEX_STARTUP_STREAMS = 16,
};

struct DexFramePlan {
	uint8_t sources[7 * 7];
	int source_count;
	int high_water;
};

static char *trim(char *text) {
	while (isspace((unsigned char)*text)) {
		text++;
	}
	char *end = text + strlen(text);
	while (end > text && isspace((unsigned char)end[-1])) {
		*--end = '\0';
	}
	return text;
}

static int parse_anim_number(const char *filename, int line, const char *text) {
	int base = 10;
	if (*text == '$') {
		base = 16;
		text++;
	} else if (*text == '%') {
		base = 2;
		text++;
	}
	char *end;
	errno = 0;
	long value = strtol(text, &end, base);
	while (isspace((unsigned char)*end)) {
		end++;
	}
	if (errno || *text == '\0' || *end != '\0' || value < 0 || value > 255) {
		error_exit("%s:%d: invalid animation value \"%s\"\n", filename, line, text);
	}
	return value;
}

static void append_anim_command(struct AnimScript *script, struct AnimCommand command) {
	if (script->count == script->capacity) {
		script->capacity = script->capacity ? script->capacity * 2 : 32;
		script->commands = xrealloc(script->commands,
			script->capacity * sizeof *script->commands);
	}
	script->commands[script->count++] = command;
}

static struct AnimScript read_anim_script(const char *filename) {
	struct AnimScript script = {.filename = filename};
	FILE *file = xfopen(filename, 'r');
	char buffer[256];
	int line = 0;
	while (fgets(buffer, sizeof buffer, file)) {
		line++;
		if (!strchr(buffer, '\n') && !feof(file)) {
			fclose(file);
			error_exit("%s:%d: animation source line is too long\n", filename, line);
		}
		char *comment = strchr(buffer, ';');
		if (comment) {
			*comment = '\0';
		}
		char *text = trim(buffer);
		if (!*text) {
			continue;
		}

		struct AnimCommand command = {.line = line};
		char first[32], second[32], extra;
		if (sscanf(text, "frame %31[^,], %31s %c", first, second, &extra) == 2) {
			command.type = ANIM_FRAME;
			command.first = parse_anim_number(filename, line, trim(first));
			command.second = parse_anim_number(filename, line, second);
		} else if (sscanf(text, "setrepeat %31s %c", first, &extra) == 1) {
			command.type = ANIM_SETREPEAT;
			command.first = parse_anim_number(filename, line, first);
			if (!command.first) {
				fclose(file);
				error_exit("%s:%d: setrepeat count must be nonzero\n", filename, line);
			}
		} else if (sscanf(text, "dorepeat %31s %c", first, &extra) == 1) {
			command.type = ANIM_DOREPEAT;
			command.first = parse_anim_number(filename, line, first);
		} else if (!strcmp(text, "endanim")) {
			command.type = ANIM_END;
		} else {
			fclose(file);
			error_exit("%s:%d: unsupported animation command \"%s\"\n",
				filename, line, text);
		}
		append_anim_command(&script, command);
	}
	if (ferror(file)) {
		fclose(file);
		error_exit("Could not read from file \"%s\": %s\n", filename, strerror(errno));
	}
	fclose(file);
	if (!script.count) {
		error_exit("%s: empty animation script\n", filename);
	}
	return script;
}

static void append_timeline_event(struct Timeline *timeline, int frame, int duration) {
	if (frame < 0 || frame >= 0xf || duration <= 0 || duration > 255) {
		error_exit("invalid generated timeline event: frame %d, duration %d\n", frame, duration);
	}
	if (timeline->count == timeline->capacity) {
		timeline->capacity = timeline->capacity ? timeline->capacity * 2 : 64;
		timeline->events = xrealloc(timeline->events,
			timeline->capacity * sizeof *timeline->events);
	}
	timeline->events[timeline->count++] = (struct TimelineEvent) {
		.frame = frame,
		.duration = duration,
	};
}

static void expand_anim_script(const struct AnimScript *script, struct Timeline *timeline) {
	int state_count = script->count * 256;
	int *seen = xmalloc(state_count * sizeof *seen);
	for (int i = 0; i < state_count; i++) {
		seen[i] = -1;
	}

	int pc = 0;
	int repeat = 0;
	while (pc >= 0 && pc < script->count) {
		int state = pc * 256 + repeat;
		if (seen[state] >= 0) {
			if (seen[state] == timeline->count) {
				free(seen);
				error_exit("%s:%d: animation has a control-only cycle\n",
					script->filename, script->commands[pc].line);
			}
			timeline->loop_start = seen[state];
			free(seen);
			return;
		}
		seen[state] = timeline->count;

		const struct AnimCommand *command = &script->commands[pc];
		switch (command->type) {
		case ANIM_FRAME:
			append_timeline_event(timeline, command->first, command->second);
			pc++;
			break;
		case ANIM_SETREPEAT:
			repeat = command->first;
			pc++;
			break;
		case ANIM_DOREPEAT:
			if (command->first >= script->count) {
				free(seen);
				error_exit("%s:%d: repeat target %d is outside the script\n",
					script->filename, command->line, command->first);
			}
			if (repeat) {
				repeat--;
			}
			if (repeat) {
				pc = command->first;
			} else {
				if (!timeline->count) {
					free(seen);
					error_exit("%s:%d: repeat exit has no visual frame to hold\n",
						script->filename, command->line);
				}
				if (timeline->events[timeline->count - 1].duration == 255) {
					append_timeline_event(timeline,
						timeline->events[timeline->count - 1].frame, 1);
				} else {
					timeline->events[timeline->count - 1].duration++;
				}
				pc++;
			}
			break;
		case ANIM_END:
			free(seen);
			return;
		}
	}
	free(seen);
	error_exit("%s: animation ran beyond its command list\n", script->filename);
}

static void append_coalesced_event(struct Timeline *timeline, int frame, int duration) {
	while (duration) {
		if (timeline->count && timeline->events[timeline->count - 1].frame == frame &&
				timeline->events[timeline->count - 1].duration < 127) {
			int room = 127 - timeline->events[timeline->count - 1].duration;
			int amount = duration < room ? duration : room;
			timeline->events[timeline->count - 1].duration += amount;
			duration -= amount;
		} else {
			int amount = duration < 127 ? duration : 127;
			append_timeline_event(timeline, frame, amount);
			duration -= amount;
		}
	}
}

static struct Timeline coalesce_timeline(const struct Timeline *source) {
	struct Timeline result = {.loop_start = -1};
	int split = source->loop_start >= 0 ? source->loop_start : source->count;
	for (int i = 0; i < split; i++) {
		append_coalesced_event(&result, source->events[i].frame,
			source->events[i].duration);
	}
	if (source->loop_start >= 0) {
		result.loop_start = result.count;
		for (int i = split; i < source->count; i++) {
			append_coalesced_event(&result, source->events[i].frame,
				source->events[i].duration);
		}
	}
	return result;
}

static void append_script_timeline(struct Timeline *destination,
		const struct AnimScript *script) {
	struct Timeline expanded = {.loop_start = -1};
	expand_anim_script(script, &expanded);
	struct Timeline coalesced = coalesce_timeline(&expanded);
	free(expanded.events);

	int base = destination->count;
	for (int i = 0; i < coalesced.count; i++) {
		append_timeline_event(destination, coalesced.events[i].frame,
			coalesced.events[i].duration);
	}
	if (coalesced.loop_start >= 0) {
		destination->loop_start = base + coalesced.loop_start;
	}
	free(coalesced.events);
}

static struct Timeline make_dex_timeline(const char *anim_filename,
		const char *idle_filename) {
	struct AnimScript anim = read_anim_script(anim_filename);
	struct AnimScript idle = read_anim_script(idle_filename);
	struct Timeline timeline = {.loop_start = -1};
	append_script_timeline(&timeline, &anim);
	if (timeline.loop_start < 0) {
		append_coalesced_event(&timeline, 0, 18);
		append_script_timeline(&timeline, &idle);
	}
	free(anim.commands);
	free(idle.commands);
	return timeline;
}

static int timeline_next_index(const struct Timeline *timeline, int index) {
	index++;
	if (index < timeline->count) {
		return index;
	}
	return timeline->loop_start;
}

static void make_dex_frame_plans(const uint8_t *tilemap, long tilemap_size,
		int width, struct DexFramePlan **result, int *num_frames, int *total_tiles) {
	int frame_size = width * width;
	if (tilemap_size % frame_size || tilemap_size < frame_size * 2) {
		error_exit("invalid animated tilemap size\n");
	}
	*num_frames = tilemap_size / frame_size - 1;
	*total_tiles = 0;
	for (long i = 0; i < tilemap_size; i++) {
		if (tilemap[i] + 1 > *total_tiles) {
			*total_tiles = tilemap[i] + 1;
		}
	}
	struct DexFramePlan *plans = xcalloc((*num_frames + 1) * sizeof *plans);
	plans[0].high_water = frame_size;
	struct DexPlanTile tiles[7 * 7];
	for (int frame_id = 1; frame_id <= *num_frames; frame_id++) {
		int count = make_dex_plan_tiles(tilemap,
			tilemap + frame_id * frame_size, width, tiles);
		plans[frame_id].high_water = frame_size;
		for (int i = 0; i < count; i++) {
			if (tiles[i].position & 0x80) {
				continue;
			}
			plans[frame_id].sources[plans[frame_id].source_count++] = tiles[i].source;
			if (tiles[i].source + 1 > plans[frame_id].high_water) {
				plans[frame_id].high_water = tiles[i].source + 1;
			}
		}
		if (plans[frame_id].high_water > *total_tiles) {
			error_exit("frame %d requires tile %d, but only %d tiles exist\n",
				frame_id, plans[frame_id].high_water - 1, *total_tiles);
		}
	}
	*result = plans;
}

static void set_timeline_targets(struct Timeline *timeline,
		const struct DexFramePlan *plans, int num_frames, int total_tiles) {
	for (int i = 0; i < timeline->count; i++) {
		int target = 0;
		int event = i;
		for (int lookahead = 0; lookahead < 3 && event >= 0; lookahead++) {
			int frame = timeline->events[event].frame;
			if (frame > num_frames) {
				error_exit("animation uses frame %d, but only %d frames exist\n",
					frame, num_frames);
			}
			if (plans[frame].high_water > target) {
				target = plans[frame].high_water;
			}
			event = timeline_next_index(timeline, event);
		}
		/* Bound startup as before; later events allow early decoding of the full dictionary. */
		timeline->events[i].target = i ? total_tiles : target;
	}
}

static void validate_timeline_structure(const char *filename,
		const struct Timeline *timeline, const struct DexFramePlan *plans,
		int total_tiles) {
	/* Timing is checked by linked-code replay, not a tiles-per-tick estimate. */
	if (!timeline->count) {
		error_exit("%s: generated timeline has no visual events\n", filename);
	}
	for (int i = 0; i < timeline->count; i++) {
		const struct TimelineEvent *event = &timeline->events[i];
		if (!event->duration || event->duration >= 128 ||
				event->target < plans[event->frame].high_water ||
				event->target > total_tiles) {
			error_exit("%s: invalid Dex timeline event %d\n", filename, i);
		}
	}
}

static void write_dex_timeline(const char *filename, const uint8_t *tilemap,
		long tilemap_size, int width, const char *anim_filename,
		const char *idle_filename) {
	struct DexFramePlan *plans;
	int num_frames, total_tiles;
	make_dex_frame_plans(tilemap, tilemap_size, width, &plans, &num_frames,
		&total_tiles);

	struct Timeline timeline = make_dex_timeline(anim_filename, idle_filename);
	set_timeline_targets(&timeline, plans, num_frames, total_tiles);
	int startup_target = width * width +
		DEX_STARTUP_STREAMS * DEX_DICTIONARY_CHUNK_TILES;
	if (startup_target > total_tiles) {
		startup_target = total_tiles;
	}
	if (timeline.events[0].target < startup_target) {
		timeline.events[0].target = startup_target;
	}
	validate_timeline_structure(filename, &timeline, plans, total_tiles);

	size_t output_size = timeline.loop_start >= 0 ? 3 : 1;
	for (int i = 0; i < timeline.count; i++) {
		output_size += timeline.events[i].duration < 16 ? 2 : 3;
	}
	uint8_t *output = xmalloc(output_size);
	size_t *event_offsets = xmalloc(timeline.count * sizeof *event_offsets);
	size_t offset = 0;
	for (int i = 0; i < timeline.count; i++) {
		event_offsets[i] = offset;
		const struct TimelineEvent *event = &timeline.events[i];
		output[offset++] = event->frame << 4 |
			(event->duration < 16 ? event->duration : 0);
		if (event->duration >= 16) {
			output[offset++] = event->duration;
		}
		output[offset++] = event->target;
	}
	if (timeline.loop_start >= 0) {
		output[offset++] = 0xf1;
		size_t rewind = offset + 2 - event_offsets[timeline.loop_start];
		if (rewind > UINT16_MAX) {
			error_exit("%s: Dex timeline loop is too large\n", filename);
		}
		output[offset++] = rewind & 0xff;
		output[offset++] = rewind >> 8;
	} else {
		output[offset++] = 0xf0;
	}
	if (offset != output_size) {
		error_exit("%s: internal timeline size mismatch\n", filename);
	}
	write_u8(filename, output, output_size);

	free(output);
	free(event_offsets);
	free(timeline.events);
	free(plans);
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
	if (argc < 2 ||
			(options.dex_timeline_filename && argc < 4)) {
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
	if (options.dex_timeline_filename) {
		write_dex_timeline(options.dex_timeline_filename, tilemap, tilemap_size,
			width, argv[2], argv[3]);
	}

	free(tilemap);
	return 0;
}
