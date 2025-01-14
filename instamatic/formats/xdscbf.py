import numpy as np

# Adapted from fabio
# https://github.com/silx-kit/fabio/blob/master/fabio/cbfimage.py


DATA_TYPES = {'signed 8-bit integer': 'int8',
              'signed 16-bit integer': 'int16',
              'signed 32-bit integer': 'int32',
              'signed 64-bit integer': 'int64',
              'unsigned 8-bit integer': 'uint8',
              'unsigned 16-bit integer': 'uint16',
              'unsigned 32-bit integer': 'uint32',
              'unsigned 64-bit integer': 'uint64',
              }

STARTER = b'\x0c\x1a\x04\xd5'


def compByteOffset(data):
    """Compress a dataset into a string using the byte_offet algorithm.

    :param data: ndarray
    :return: string/bytes with compressed data

    test = np.array([0,1,2,127,0,1,2,128,0,1,2,32767,0,1,2,32768,0,1,2,2147483647,0,1,2,2147483648,0,1,2,128,129,130,32767,32768,128,129,130,32768,2147483647,2147483648])
    """
    flat = np.ascontiguousarray(data.ravel(), np.int64)
    delta = np.zeros_like(flat)
    delta[0] = flat[0]
    delta[1:] = flat[1:] - flat[:-1]
    mask = abs(delta) > 127
    exceptions = np.nonzero(mask)[0]
    if np.little_endian:
        byteswap = False
    else:
        byteswap = True
    start = 0
    binary_blob = b''
    for stop in exceptions:
        if stop - start > 0:
            binary_blob += delta[start:stop].astype(np.int8).tobytes()
        exc = delta[stop]
        absexc = abs(exc)
        if absexc > 2147483647:  # 2**31-1
            binary_blob += b'\x80\x00\x80\x00\x00\x00\x80'
            if byteswap:
                binary_blob += delta[stop:stop + 1].byteswap().tobytes()
            else:
                binary_blob += delta[stop:stop + 1].tobytes()
        elif absexc > 32767:  # 2**15-1
            binary_blob += b'\x80\x00\x80'
            if byteswap:
                binary_blob += delta[stop:stop + 1].astype(np.int32).byteswap().tobytes()
            else:
                binary_blob += delta[stop:stop + 1].astype(np.int32).tobytes()
        else:  # >127
            binary_blob += b'\x80'
            if byteswap:
                binary_blob += delta[stop:stop + 1].astype(np.int16).byteswap().tobytes()
            else:
                binary_blob += delta[stop:stop + 1].astype(np.int16).tobytes()
        start = stop + 1
    if start < delta.size:
        binary_blob += delta[start:].astype(np.int8).tobytes()
    return binary_blob


def write(fname, data, header={}):
    """write the file in CBF format.

    :param str fname: name of the file
    """
    if data is not None:
        dim2, dim1 = data.shape
    else:
        raise RuntimeError('CBF image contains no data')
    binary_blob = compByteOffset(data)
    dtype = 'Unknown'
    for key, value in DATA_TYPES.items():
        if value == data.dtype:
            dtype = key
    binary_block = [b'###CBF: Version July 2008 generated by XDS',
                    b'',
                    b'data_a.cbf',
                    b'',
                    b'_array_data.header_convention "XDS special"',
                    b'_array_data.header_contents',
                    b';',
                    b';',
                    b'',
                    b'_array_data.data',
                    b';',
                    b'--CIF-BINARY-FORMAT-SECTION--',
                    b'Content-Type: application/octet-stream;',
                    b'     conversions="x-CBF_BYTE_OFFSET"',
                    b'Content-Transfer-Encoding: BINARY',
                    np.string_('X-Binary-Size: %d' % (len(binary_blob))),
                    b'X-Binary-ID: 1',
                    np.string_('X-Binary-Element-Type: "%s"' % (dtype)),
                    b'X-Binary-Element-Byte-Order: LITTLE_ENDIAN',
                    np.string_('X-Binary-Number-of-Elements: %d' % (dim1 * dim2)),
                    np.string_('X-Binary-Size-Fastest-Dimension: %d' % dim1),
                    np.string_('X-Binary-Size-Second-Dimension: %d' % dim2),
                    b'X-Binary-Size-Padding: 1',
                    b'',
                    STARTER + binary_blob,
                    b'',
                    b'--CIF-BINARY-FORMAT-SECTION----']

    cbf = b'\r\n'.join(binary_block)
    with open(fname, 'wb') as out_file:
        out_file.write(cbf)


if __name__ == '__main__':
    arr = np.arange(128 * 128).reshape(128, 128)
    write('a.cbf', arr)
    print('run `xdsviewer a.cbf`')
