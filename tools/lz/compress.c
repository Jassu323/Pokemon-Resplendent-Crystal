#include "proto.h"

struct command * compress (const unsigned char * data, unsigned short * size, unsigned method) {
  unsigned char * bitflipped = malloc(*size);
  unsigned current;
  for (current = 0; current < *size; current ++) bitflipped[current] = bit_flipping_table[data[current]];
  const struct compressor * compressor = compressors;
  struct command * result;
  if (method < COMPRESSION_METHODS) {
    while (method >= compressor -> methods) method -= (compressor ++) -> methods;
    result = compressor -> function(data, bitflipped, size, method);
  } else {
    struct command * compressed_sequences[COMPRESSION_METHODS];
    unsigned short lengths[COMPRESSION_METHODS];
    unsigned flags = 0;
    for (current = 0; current < COMPRESSION_METHODS; current ++) {
      lengths[current] = *size;
      if (flags == compressor -> methods) {
        flags = 0;
        compressor ++;
      }
      compressed_sequences[current] = compressor -> function(data, bitflipped, lengths + current, flags ++);
    }
    result = select_optimal_sequence(compressed_sequences, lengths, size);
    for (current = 0; current < COMPRESSION_METHODS; current ++) free(compressed_sequences[current]);
  }
  free(bitflipped);
  return result;
}
