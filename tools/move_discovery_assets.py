"""Independent decoder and private fixture writer for the discovery extension."""
import binascii


def address(symbols, name):
    bank, value = symbols[name]
    return bank * 8192 + value - 0xa000


def identity(data, symbols, prefix):
    start = address(symbols, prefix + 'PlayerData')
    secret = start + symbols['wSecretID'][1] - symbols['wPlayerData'][1]
    return bytes(data[start:start + 2] + data[secret:secret + 2])


def encode_record(data, symbols, prefix, bitmap, version=1):
    if not 1 <= len(bitmap) <= 128:
        raise ValueError('Record does not fit reserved padding')
    parent = address(symbols, prefix + 'Checksum')
    metadata = b'MD' + bytes((version, len(bitmap))) + bytes(data[parent:parent + 2])
    crc = binascii.crc_hqx(metadata + identity(data, symbols, prefix) + bitmap, 0xffff)
    return metadata + crc.to_bytes(2, 'little') + bitmap


def decode_record(data, symbols, prefix):
    at = address(symbols, prefix + 'MoveDiscovery')
    header = bytes(data[at:at + 8])
    if header[:2] != b'MD':
        return dict(status='legacy', bitmap=None)
    if not 1 <= header[3] <= 128:
        return dict(status='damaged', bitmap=None)
    bitmap = bytes(data[at + 8:at + 8 + header[3]])
    expected = encode_record(data, symbols, prefix, bitmap, header[2])
    if expected != bytes(data[at:at + len(expected)]):
        return dict(status='damaged', bitmap=None)
    if (header[2], header[3]) != (1, 64):
        return dict(status='unsupported', bitmap=None)
    return dict(status='valid', bitmap=bitmap)


def seed_records(data, symbols, bitmap):
    result = bytearray(data)
    for prefix in ('s', 'sBackup'):
        at = address(symbols, prefix + 'MoveDiscovery')
        result[at:at + 72] = encode_record(result, symbols, prefix, bitmap)
    return bytes(result)


def rebind_fixture(before, after, symbols):
    """Keep valid flags when a private fixture deliberately changes core fields."""
    if 'sMoveDiscovery' not in symbols:
        return bytes(after)
    result = bytearray(after)
    for prefix in ('s', 'sBackup'):
        record = decode_record(before, symbols, prefix)
        if record['status'] == 'valid':
            at = address(symbols, prefix + 'MoveDiscovery')
            result[at:at + 72] = encode_record(result, symbols, prefix, record['bitmap'])
    return bytes(result)


def move_bitmap(indices):
    result = bytearray(64)
    for index in indices:
        if not 1 <= index <= 512:
            raise ValueError('Invalid permanent index')
        result[(index - 1) // 8] |= 1 << ((index - 1) & 7)
    return bytes(result)
