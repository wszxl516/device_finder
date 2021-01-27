"""
    Byte  0 -  3:   magic
                    QCOW magic string ("QFI\xfb")

          4 -  7:   version
                    Version number (valid values are 2 and 3)

          8 - 15:   backing_file_offset
                    Offset into the image file at which the backing file name
                    is stored (NB: The string is not null terminated). 0 if the
                    image doesn't have a backing file.

                    Note: backing files are incompatible with raw external data
                    files (auto-clear feature bit 1).

         16 - 19:   backing_file_size
                    Length of the backing file name in bytes. Must not be
                    longer than 1023 bytes. Undefined if the image doesn't have
                    a backing file.

         20 - 23:   cluster_bits
                    Number of bits that are used for addressing an offset
                    within a cluster (1 << cluster_bits is the cluster size).
                    Must not be less than 9 (i.e. 512 byte clusters).

                    Note: qemu as of today has an implementation limit of 2 MB
                    as the maximum cluster size and won't be able to open images
                    with larger cluster sizes.

                    Note: if the image has Extended L2 Entries then cluster_bits
                    must be at least 14 (i.e. 16384 byte clusters).

         24 - 31:   size
                    Virtual disk size in bytes.

                    Note: qemu has an implementation limit of 32 MB as
                    the maximum L1 table size.  With a 2 MB cluster
                    size, it is unable to populate a virtual cluster
                    beyond 2 EB (61 bits); with a 512 byte cluster
                    size, it is unable to populate a virtual size
                    larger than 128 GB (37 bits).  Meanwhile, L1/L2
                    table layouts limit an image to no more than 64 PB
                    (56 bits) of populated clusters, and an image may
                    hit other limits first (such as a file system's
                    maximum size).

         32 - 35:   crypt_method
                    0 for no encryption
                    1 for AES encryption
                    2 for LUKS encryption

         36 - 39:   l1_size
                    Number of entries in the active L1 table

         40 - 47:   l1_table_offset
                    Offset into the image file at which the active L1 table
                    starts. Must be aligned to a cluster boundary.

         48 - 55:   refcount_table_offset
                    Offset into the image file at which the refcount table
                    starts. Must be aligned to a cluster boundary.

         56 - 59:   refcount_table_clusters
                    Number of clusters that the refcount table occupies

         60 - 63:   nb_snapshots
                    Number of snapshots contained in the image

         64 - 71:   snapshots_offset
                    Offset into the image file at which the snapshot table
                    starts. Must be aligned to a cluster boundary.
"""
import struct
import ctypes
from collections import namedtuple
import os

img = namedtuple('Image', ['format', 'size', 'virtual_size', 'version'])


class Qcow2(ctypes.BigEndianStructure):
    _fields_ = [('magic', ctypes.c_char * 4),
                ('version', ctypes.c_uint32),
                ('backing_f_offset', ctypes.c_uint64),
                ('backing_file_size', ctypes.c_uint32),
                ('cluster_bits', ctypes.c_uint32),
                ('size', ctypes.c_uint64),
                ('crypt_method', ctypes.c_uint32),
                ('l1_size', ctypes.c_uint32),
                ('l1_table_offset', ctypes.c_uint32),
                ('refcount_table_offset', ctypes.c_uint64),
                ('refcount_table_clusters', ctypes.c_uint32),
                ('nb_snapshots', ctypes.c_uint32),
                ('snapshots_offset', ctypes.c_uint64)]


class Image(img):
    def __new__(cls, img_file):
        header_size = ctypes.sizeof(Qcow2)
        with open(img_file, 'rb')as fp:
            header_data = fp.read(header_size)
        q = Qcow2.from_buffer_copy(bytes(header_data))
        stat = os.stat(img_file)
        if q.magic == b'QFI\xfb':
            fmt = 'qcow2'
            virtual_size = q.size
            real_size = stat.st_size
        else:
            fmt = 'raw'
            virtual_size = stat.st_size
            real_size = stat.st_blksize * stat.st_blocks

        return img(format=fmt, size=real_size, virtual_size=virtual_size, version=q.version)


print(Image('r.img'))
print(Image('q.img'))