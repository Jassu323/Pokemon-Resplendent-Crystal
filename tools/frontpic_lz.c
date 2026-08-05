#include "lz/proto.h"

#define TILE_SIZE 16
#define TAIL_CHUNK_TILES 16

static unsigned read_dimension(const char *filename) {
	FILE *file = fopen(filename, "rb");
	if (!file)
		error_exit(1, "could not open file %s for reading", filename);
	int byte = fgetc(file);
	fclose(file);
	if (byte == EOF)
		error_exit(1, "file %s is empty", filename);
	return byte & 0xf;
}

static void write_compressed_stream(FILE *file, const unsigned char *data, unsigned short size) {
	unsigned short command_count = size;
	struct command *commands = compress(data, &command_count, COMPRESSION_METHODS);
	write_commands_to_stream(file, commands, command_count, data);
	free(commands);
}

int main(int argc, char **argv) {
	if (argc != 4)
		error_exit(3, "usage: %s front.animated.2bpp front.dimensions output", argv[0]);

	unsigned short size;
	unsigned char *data = read_file_into_buffer(argv[1], &size);
	unsigned dimension = read_dimension(argv[2]);
	unsigned base_size = dimension * dimension * TILE_SIZE;
	if (!dimension || size % TILE_SIZE || base_size > size || size / TILE_SIZE > 0xff)
		error_exit(1, "invalid frontpic data in %s", argv[1]);

	FILE *output = fopen(argv[3], "wb");
	if (!output)
		error_exit(1, "could not open file %s for writing", argv[3]);
	if (putc(size / TILE_SIZE, output) == EOF)
		error_exit(1, "could not write frontpic header to %s", argv[3]);

	write_compressed_stream(output, data, base_size);
	for (unsigned offset = base_size; offset < size;) {
		unsigned chunk_size = size - offset;
		if (chunk_size > TAIL_CHUNK_TILES * TILE_SIZE)
			chunk_size = TAIL_CHUNK_TILES * TILE_SIZE;
		write_compressed_stream(output, data + offset, chunk_size);
		offset += chunk_size;
	}

	if (fclose(output))
		error_exit(1, "could not close output file %s", argv[3]);
	free(data);
	return 0;
}
