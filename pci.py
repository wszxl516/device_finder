#!/usr/bin/python3
from collections import UserDict
import os
import glob


class PCIInfo:
    _instance = None
    pci_data = {}

    def __new__(cls, *args, **kwargs):
        if getattr(cls, '_instance') is None:
            cls._instance = super(PCIInfo, cls).__new__(cls, *args, **kwargs)
            cls._init()
        return cls._instance

    @staticmethod
    def _init():
        PCIInfo.pci_data = {}
        for ids in ['/usr/share/misc/pci.ids', '/usr/share/hwdata/pci.ids']:
            if not os.path.exists(ids):
                continue
            with open(ids)as fp:
                lines = fp.readlines()
                for line in lines:
                    line = line.strip('\n')
                    if line.startswith('#') or not line.strip():
                        continue
                    elif line[:2] == '\t\t':
                        try:
                            sub_vendor, sub_device, subsystem_name = line.split(maxsplit=2)
                        except ValueError:
                            sub_device, subsystem_name = line.split(maxsplit=1)
                            sub_vendor = vendor_id
                        if sub_vendor not in PCIInfo.pci_data[vendor_id]['subsystem']:
                            PCIInfo.pci_data[vendor_id]['subsystem'][sub_vendor] = {}
                        PCIInfo.pci_data[vendor_id]['subsystem'][sub_vendor][sub_device] = subsystem_name
                    elif line[:1] == '\t':
                        device_id, device_name = line.split(maxsplit=1)
                        PCIInfo.pci_data[vendor_id]['device'][device_id] = device_name.strip()
                    else:
                        vendor_id, vendor_name = line.split(maxsplit=1)
                        if vendor_id not in PCIInfo.pci_data:
                            PCIInfo.pci_data[vendor_id] = {'name': vendor_name.strip(),
                                                           'device': {},
                                                           'subsystem': {}}

    def find(self, vendor_id, device_id, sub_vendor=None, sub_device=None):
        vendor_data = self.pci_data.get(vendor_id, {})
        if sub_vendor is not None and sub_device is not None:
            subsystem_name = self.pci_data.get(vendor_id, {}).get('subsystem', {}) \
                .get(sub_vendor, {}).get(sub_device, '')
        else:
            subsystem_name = ''
        vendor_name = vendor_data.get('name', '')
        device_name = vendor_data.get('device', {}).get(device_id, '')
        return vendor_name, device_name, subsystem_name


class ModuleAlias:
    _instance = None
    data = {}

    def __new__(cls, *args, **kwargs):
        if getattr(cls, '_instance') is None:
            cls._instance = super(ModuleAlias, cls).__new__(cls, *args, **kwargs)
            cls._init()
        return cls._instance

    @staticmethod
    def _init():
        ModuleAlias._module_alias_path = os.path.join('/lib/modules', os.uname().release, 'modules.alias')
        if not os.path.exists(ModuleAlias._module_alias_path):
            ModuleAlias._module_alias_path = None
            ModuleAlias.data = []
        else:
            with open(ModuleAlias._module_alias_path)as fp:
                ModuleAlias.data = fp.readlines()

    def find(self, module_alias: str):
        modules = []
        for line in self.data:
            if line.startswith('#'):
                continue
            if not self.type_match(line, module_alias):
                continue
            _pattern, _module_name = self._parse(line)
            if self.match(module_alias, _pattern):
                if _module_name not in modules:
                    modules.append(_module_name)
        return modules

    @staticmethod
    def type_match(line, pattern):
        if line[6:].startswith(pattern.split(':')[0]):
            return True
        return False

    @staticmethod
    def _parse(line):
        data = line.split()
        _pattern, _module_name = None, None
        if data.__len__() > 3:
            _pattern = ''.join(data[1:-1])
            _module_name = data[-1]
        else:
            _, _pattern, _module_name = data
        return _pattern, _module_name

    @staticmethod
    def match(string: str, pattern: str):
        if string == pattern:
            return True
        for pat in pattern.split('*'):
            if pat not in string:
                return False
        return True


class PCIDevice(UserDict):
    def __init__(self, dev_path: str, *args, **kwargs):
        super(PCIDevice, self).__init__(*args, **kwargs)
        self.info = PCIInfo()
        self.dev_path = dev_path
        self.domain, self.bus, device = dev_path.split(':')
        # PCI domain, bus number
        self.device_number, self.device_function = device.split('.')
        # the device number, PCI device function
        keys = ['class',
                # PCI class (ascii, ro)
                # 'config',
                # PCI config space (binary, rw)
                'device',
                # PCI device (ascii, ro)
                'enable',
                # Whether the device is enabled (ascii, rw)
                'irq',
                # IRQ number (ascii, ro)
                'local_cpus',
                # nearby CPU mask (cpumask, ro)
                # 'remove',
                # remove device from kernel’s list (ascii, wo)
                'resource',
                # PCI resource host addresses (ascii, ro)
                # resource0..N	PCI resource N, if present (binary, mmap, rw[1])
                # resource0_wc..N_wc	PCI WC map resource N, if prefetchable (binary, mmap)
                'revision',
                # PCI revision (ascii, ro)
                # 'rom',
                # PCI ROM resource, if present (binary, ro)
                'subsystem_device',
                # PCI subsystem device (ascii, ro)
                'subsystem_vendor',
                # PCI subsystem vendor (ascii, ro)
                'vendor',
                # PCI vendor (ascii, ro)
                'modalias',
                'max_link_speed',
                # GT/s
                'max_link_width'
                ]
        m = ModuleAlias()
        for k in keys:
            self.__setitem__(k, self.read_attr(k))
        self.driver = self.read_driver()
        self.dev_name = ' '.join(self.info.find(self.vendor[2:],
                                                self.device[2:],
                                                self.subsystem_vendor[2:],
                                                self.subsystem_device[2:])
                                 )
        self.sub_name = ' '.join(self.info.find(self.subsystem_vendor[2:],
                                                self.subsystem_device[2:])
                                 )
        self.modules = m.find(self.modalias)
        self.dev_type_name, self.dev_type = self.get_dev_type()
        self.devices = self.get_dev()

    def __getattr__(self, item):
        return self.get(item, '')

    def get_dev(self):
        dev_pats = {
            '01': ['ata[0-9]/host[0-9]/target[0-9]:[0-9]:[0-9]/[0-9]:[0-9]:[0-9]:[0-9]/block/*'],
            '02': ['net/*'],
            '0c': ['usb*', 'i2c*'],
            '06': ['INT*/firmware_node', 'PNP*/firmware_node']
        }
        devices = []
        for dt in self.dev_type:
            dev_pat = dev_pats.get(dt, None)
            if dev_pat is not None:
                for pat in dev_pat:
                    interface_path = os.path.join(self.dev_path, pat)
                    for i in glob.glob(interface_path):
                        if os.path.islink(i):
                            i = os.readlink(i)
                        device = os.path.split(i)[-1]
                        if device not in devices:
                            devices.append(device)
        return devices

    def get_dev_type(self):
        types = {
            '00': '',
            # 'Unclassified device'
            '01': 'Mass storage controller',
            '02': 'Network controller',
            '03': 'Display controller',
            '04': 'Multimedia controller',
            '05': 'Memory controller',
            '06': 'Bridge',
            '07': 'Communication controller',
            '08': 'Generic system peripheral',
            '09': 'Input device controller',
            '0a': 'Docking station',
            '0b': 'Processor',
            '0c': 'Serial bus controller',
            '0d': 'Wireless controller',
            '0e': 'Intelligent controller',
            '0f': 'Satellite communications controller',
            '10': 'Encryption controller',
            '11': 'Signal processing controller',
            '12': 'Processing accelerators',
            '13': 'Non-Essential Instrumentation',
            '15': '',
            '40': 'Coprocessor',
            '64': '',
            'ff': ''
            # 'Unassigned class'
        }
        class_type = self.get('class')[2:]
        dev_type_name = []
        dev_types = []
        for t in range(0, class_type.__len__(), 2):
            type_num = class_type[t:t + 2]
            dev_type = types.get(type_num, '')
            if dev_type != '' and dev_type not in dev_type_name:
                dev_type_name.append(dev_type)
                dev_types.append(type_num)
        return dev_type_name, dev_types

    def read_driver(self) -> str:
        driver_path = os.path.join(self.dev_path, 'driver')
        if os.path.exists(driver_path):
            return os.path.basename(os.readlink(driver_path))
        return ''

    def read_attr(self, name: str, path=None):
        if path is None:
            path = os.path.join(self.dev_path, name)
        else:
            path = os.path.join(path, name)
        if not os.path.exists(path):
            return ''
        with open(path, 'rb')as fp:
            attr = fp.readline().strip()
            try:
                attr = attr.decode()
            except UnicodeDecodeError:
                pass
        return attr

    def __repr__(self):
        return '<PCIDevice {} {} {} {}' \
               '\n\t{}: {} {} {} (rev {})' \
               '\n\tsubsystem: {} {} {}' \
               '\n\tenable :{}' \
               '\n\tirq: {}' \
               '\n\tcpu: {} ' \
               '\n\tdevice: {}' \
               '\n\tdriver: {} ' \
               '\n\tmodules: {}' \
            .format(self.__getitem__('class'),
                    self.dev_type_name,
                    self.max_link_speed,
                    self.max_link_width,
                    self.dev_path,
                    self.vendor,
                    self.device,
                    self.dev_name, self.revision,
                    self.subsystem_vendor,
                    self.subsystem_device,
                    self.sub_name,
                    self.enable,
                    self.irq,
                    self.local_cpus,
                    self.devices,
                    self.driver,
                    self.modules)


def find_pci():
    pci_devices = glob.glob('/sys/bus/pci/devices/*')
    print(pci_devices.__len__())
    for pci_path in pci_devices:
        pci = PCIDevice(pci_path)
        print(pci)


if __name__ == '__main__':
    find_pci()
