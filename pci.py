from collections import UserDict
import os
import glob
import pprint


class PCIInfo:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '_instance'):
            cls._instance = super(PCIInfo, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.pci_data = {}
        with open('/usr/share/hwdata/pci.ids')as fp:
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
                    if sub_vendor not in self.pci_data[vendor_id]['subsystem']:
                        self.pci_data[vendor_id]['subsystem'][sub_vendor] = {}
                    self.pci_data[vendor_id]['subsystem'][sub_vendor][sub_device] = subsystem_name
                elif line[:1] == '\t':
                    device_id, device_name = line.split(maxsplit=1)
                    self.pci_data[vendor_id]['device'][device_id] = device_name.strip()
                else:
                    vendor_id, vendor_name = line.split(maxsplit=1)
                    if vendor_id not in self.pci_data:
                        self.pci_data[vendor_id] = {'name': vendor_name.strip(),
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


class PCIDevice(UserDict):
    def __init__(self, dev_path: str, *args, **kwargs):
        super(PCIDevice, self).__init__(*args, **kwargs)
        self.info = PCIInfo()
        self._prefix = '/sys/bus/pci/devices'
        self.dev_path = dev_path
        self.domain, self.bus, device = dev_path.split(':')
        # PCI domain, bus number
        self.device_number, self.device_function = device.split('.')
        # the device number, PCI device function
        keys = ['class',
                # PCI class (ascii, ro)
                'config',
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
                'modalias'
                ]
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
        self.modules = self.find_modules()
        self.dev_type_name, self.dev_type = self.get_dev_type()
        # TODO:
        # get sub device net，storage

    def __getattr__(self, item):
        return self.get(item, '')

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
            type_num = class_type[t:t+2]
            dev_type = types.get(type_num, '')
            if dev_type != '':
                dev_type_name.append(dev_type)
                dev_types.append(type_num)
        return dev_type_name, dev_types

    def find_modules(self):
        _, data = self.modalias.split(':v', 1)
        v, data = data.split('d', 1)
        d, data = data.split('sv', 1)
        sv, data = data.split('sd', 1)
        # sub vendor
        sd, data = data.split('bc', 1)
        # sub device
        bc, data = data.split('sc', 1)
        # base class
        sc, data = data.split('i', 1)
        # sub class
        i = data
        modules = []
        with open(os.path.join('/lib/modules', os.uname().release, 'modules.alias'))as fp:
            for line in fp:
                if 'v' + v in line and 'bc' + bc in line and 'sc' + sc in line and 'i' + i in line:
                    module = line.split()[-1]
                    if module not in modules:
                        modules.append(module)
        return modules

    def read_driver(self) -> str:
        driver_path = os.path.join(self._prefix, self.dev_path, 'driver')
        if os.path.exists(driver_path):
            return os.path.basename(os.readlink(driver_path))
        return ''

    def read_attr(self, name: str, path=None):
        if path is None:
            path = os.path.join(self._prefix, self.dev_path, name)
        else:
            path = os.path.join(path, name)
        if not os.path.exists(path):
            return '0'
        with open(path, 'rb')as fp:
            attr = fp.readline().strip()
            try:
                attr = attr.decode()
            except UnicodeDecodeError:
                pass
        return attr

    def __repr__(self):
        return '<PCIDevice {} {}' \
               '\n\t{}: {} {} {} (rev {})' \
               '\n\tsubsystem: {} {} {}' \
               '\n\tenable :{}' \
               '\n\tirq: {}' \
               '\n\tcpu: {} ' \
               '\n\tdriver: {} ' \
               '\n\tmodules: {}' \
            .format(self.__getitem__('class'),
                    self.dev_type_name,
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
                    self.driver,
                    self.modules)


def find_pci():
    pci_devices = glob.glob('/sys/bus/pci/devices/*')
    print(pci_devices.__len__())
    for pci_path in pci_devices:
        pci = PCIDevice(pci_path.split('/')[-1])
        print(pci.__repr__())


find_pci()
