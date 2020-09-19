#!/usr/bin/python3
from collections import UserDict
import os
import pprint
import glob
from pci import ModuleAlias
SECTOR_SIZE = 512


class BlockDevice(UserDict):
    def __init__(self, dev_path: str, *args, **kwargs):
        self.dev_path = dev_path
        self.dev_name = os.path.split(self.dev_path)[-1]
        super(BlockDevice, self).__init__(*args, **kwargs)
        module = ModuleAlias()
        keys = ['alignment_offset',
                'discard_alignment',
                'hidden',
                'size',
                'uevent',
                'events',
                'capability',
                'events_async',
                'inflight',
                'range',
                'stat',
                'dev',
                'events_poll_msecs',
                'removable',
                'ext_range',
                'ro',
                'device/vendor',
                'device/model',
                'device/modalias',
                'device/rev']
        for key in keys:
            value = self.read_attr(key)
            if key == 'size':
                value = int(value.strip()) * SECTOR_SIZE
            self.__setitem__(key.split('/')[-1], value)
        self.__setitem__('module', module.find(self.modalias))
        self.__setitem__('stat', self.stat_parse())
        self.__setitem__('id', self.parse_wwn())
        self.part_parse()

    def __getattr__(self, item):
        return self.get(item, '')

    def parse_wwn(self):
        disk_id = []
        for dev_name in glob.glob('/dev/disk/by-id/*'):
            if os.path.split(os.readlink(dev_name))[-1] == self.dev_name:
                disk_id.append(os.path.split(dev_name)[-1])
        return disk_id

    @staticmethod
    def uuid_parse(part_name):
        for dev_name in glob.glob('/dev/disk/by-uuid/*'):
            if os.path.split(os.readlink(dev_name))[-1] == part_name:
                return os.path.split(dev_name)[-1]

    def part_parse(self):
        part_path = os.path.join(self.dev_path, self.dev_name + '*')
        parts = []
        for part in glob.glob(part_path):
            part_info = {}
            keys = ['alignment_offset',
                    'discard_alignment',
                    'inflight',
                    'size',
                    'stat',
                    'dev',
                    'partition',
                    'ro',
                    'start',
                    'uevent']
            part_name = os.path.split(part)[-1]
            for key in keys:
                value = self.read_attr(key, part)
                if key == 'stat':
                    value = self.stat_parse(value)
                if key == 'size':
                    value = int(value) * SECTOR_SIZE
                part_info[key] = value
            part_info['uuid'] = self.uuid_parse(part_name)
            part_info['name'] = part_name
            parts.append(part_info)
            self.__setitem__('part', parts)

    def stat_parse(self, stat=None):
        """
        read I/Os	    requests	    number of read I/Os processed
        read merges	    requests	    number of read I/Os merged with in-queue I/O
        read sectors    sectors	        number of sectors read
        read ticks	    milliseconds	total wait time for read requests
        write I/Os	    requests	    number of write I/Os processed
        write merges    requests	    number of write I/Os merged with in-queue I/O
        write sectors   sectors	        number of sectors written
        write ticks	    milliseconds	total wait time for write requests
        in_flight	    requests	    number of I/Os currently in flight
        io_ticks	    milliseconds	total time this block device has been active
        time_in_queue   milliseconds	total wait time for all requests
        discard I/Os	requests	    number of discard I/Os processed
        discard merges	requests	    number of discard I/Os merged with in-queue I/O
        discard sectors	sectors	        number of sectors discarded
        discard ticks	milliseconds	total wait time for discard requests
        flush I/Os	    requests	    number of flush I/Os processed
        flush ticks
        :return:
        """
        keys = [
            'read',
            'read_merge',
            'read_sector',
            'read_ticks',
            'write',
            'write_merge',
            'write_sector',
            'write_tick',
            'in_flight',
            'io_ticks',
            'time_in_queue',
            'discard',
            'discard_merge',
            'discard_sector',
            'discard_tick',
            'flush',
            'flush_tick',
        ]
        if stat is None:
            values = self.stat.split()
        else:
            values = stat.split()
        values = [int(v) for v in values]
        return dict(zip(keys, values))

    def read_attr(self, name: str, path=None):
        if path is None:
            path = os.path.join(self.dev_path, name)
        else:
            path = os.path.join(path, name)
        if not os.path.exists(path):
            return ''
        with open(path, 'r')as fp:
            attr = fp.readline().strip()
        return attr

    def __str__(self):
        string = '<BlockDevice: {name} mod: {driver} size: {size:e} dev: {dev} part: {part_num}>'
        return string.format(name=self.dev_name,
                             driver=','.join(self.module),
                             size=self.size,
                             dev=self.dev,
                             part_num=self.part.__len__())

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    for blk_path in glob.glob('/sys/block/*'):
        pprint.pprint(BlockDevice(blk_path))
