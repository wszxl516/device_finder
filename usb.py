#!/usr/bin/python3
import glob
import pprint
from collections import UserDict
import os
import sys


class USBInfo:
    modes = type('usb_ids',
                 (),
                 dict(zip(('Vendor', 'Class', 'Misc'), range(3)))
                 )
    usbids = [
        "/usr/share/hwdata/usb.ids",
        "/usr/share/usb.ids",
        "/usr/share/libosinfo/usb.ids",
        "/usr/share/kcmusb/usb.ids",
    ]
    usb_vendors = {}
    usb_products = {}
    usb_classes = {}
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '_instance'):
            cls._instance = super(USBInfo, cls).__new__(cls, *args, **kwargs)
            cls.parse_usb_ids()
        return cls._instance

    @staticmethod
    def open_read_ign(fn):
        try:
            return open(fn, 'r', errors='ignore')
        except IOError:
            return open(fn, 'r')

    @staticmethod
    def is_hex_digit(string):
        for dg in string:
            if not dg.isdigit() and dg not in 'abcdef':
                return False
        return True

    @staticmethod
    def parse_usb_ids():
        vid = 0
        did = 0
        mode = USBInfo.modes.Vendor
        c_str = ""
        for unm in USBInfo.usbids:
            if os.path.exists(unm):
                break
        for ln in USBInfo.open_read_ign(unm).readlines():
            if ln[0] == '#':
                continue
            ln = ln.rstrip('\n')
            if len(ln) == 0:
                continue
            if USBInfo.is_hex_digit(ln[0:4]):
                mode = USBInfo.modes.Vendor
                vid = int(ln[:4], 16)
                USBInfo.usb_vendors[vid] = ln[6:]
                continue
            if ln[0] == '\t' and USBInfo.is_hex_digit(ln[1:3]):
                # usb.ids has a.stat device id of 01xy, sigh
                if ln[3:5] == "xy":
                    did = int(ln[1:3], 16) * 256
                else:
                    did = int(ln[1:5], 16)
                # USB devices
                if mode == USBInfo.modes.Vendor:
                    USBInfo.usb_products[vid, did] = ln[7:]
                    continue
                elif mode == USBInfo.modes.Class:
                    nm = ln[5:]
                    if nm != "Unused":
                        str_g = c_str + ":" + nm
                    else:
                        str_g = c_str + ":"
                    USBInfo.usb_classes[vid, did, -1] = str_g
                    continue
            if ln[0] == 'C':
                mode = USBInfo.modes.Class
                cid = int(ln[2:4], 16)
                c_str = ln[6:]
                USBInfo.usb_classes[cid, -1, -1] = c_str
                continue
            if mode == USBInfo.modes.Class and ln[0] == '\t' and ln[1] == '\t' and USBInfo.is_hex_digit(ln[2:4]):
                prid = int(ln[2:4], 16)
                USBInfo.usb_classes[cid, did, prid] = ln[6:]
                continue
            mode = USBInfo.modes.Misc
        USBInfo.usb_classes[0xFF, 0xFF, 0xFF] = "Vendor Specific"

    @staticmethod
    def find_usb_class(cid, sid, pid):
        """
        Return USB protocol from usbclasses list
        lnlst = len(USBInfo.usbclasses)
        """
        cls = USBInfo.usb_classes.get((cid, sid, pid)) \
              or USBInfo.usb_classes.get((cid, sid, -1)) \
              or USBInfo.usb_classes.get((cid, -1, -1))
        if cls:
            return str(cls)
        return ""

    @staticmethod
    def find_storage(hostno):
        """
        Return SCSI block dev names for host
        """
        res = ""
        for ent in os.listdir("/sys/class/scsi_device/"):
            (host, bus, tgt, lun) = ent.split(":")
            if host == hostno:
                try:
                    for ent2 in os.listdir("/sys/class/scsi_device/%s/device/block" % ent):
                        res += ent2 + " "
                except FileNotFoundError:
                    pass
        return res

    @staticmethod
    def add_drv(path, drv_nm):
        res = ""
        try:
            for e2 in os.listdir(os.path.join(path, drv_nm)):
                if e2[0:len(drv_nm)] == drv_nm:
                    res += e2 + ' '
            try:
                if res:
                    res += os.path.basename(os.readlink(os.path.join(path, 'driver')))
            except (FileNotFoundError, OSError):
                pass
        except (FileNotFoundError, OSError):
            pass
        return res

    @staticmethod
    def find_usb_prod(vid, pid):
        """Return device name from USB Vendor:Product list"""
        vendor = USBInfo.usb_vendors.get(vid)
        if vendor:
            str_g = str(vendor)
        else:
            return ""
        product = USBInfo.usb_products.get((vid, pid))
        if product:
            return str_g + " " + str(product)
        return str_g

    @staticmethod
    def find_dev(driver, usb_name):
        """
        Return pseudo devname that's driven by driver
        """
        dev_lst = [
            'host',  # usb-storage
            'video4linux/video',  # uvcvideo et al.
            'sound/card',  # snd-usb-audio
            'net/',  # cdc_ether, ...
            'input/input',  # usbhid
            'usb:hiddev',  # usb hid
            'bluetooth/hci',  # btusb
            'ttyUSB',  # btusb
            'tty/',  # cdc_acm
            'usb:lp',  # usblp
            'usb/lp',  # usblp
            'usb/',  # hiddev, usblp
            'usbhid',  # hidraw
        ]
        prefix = ""
        res = ""
        for nm in dev_lst:
            dir_nm = prefix + usb_name
            prep = ""
            idx = nm.find('/')
            if idx != -1:
                prep = nm[:idx + 1]
                dir_nm += "/" + nm[:idx]
                nm = nm[idx + 1:]
            ln = len(nm)
            try:
                for ent in os.listdir(dir_nm):
                    if ent[:ln] == nm:
                        res += prep + ent + " "
                        if nm == "host":
                            res += "(" + USBInfo.find_storage(ent[ln:])[:-1] + ")"
            except (FileNotFoundError, OSError):
                pass
        dev_info = [res]
        if driver == "usbhid":
            pat = '[0-9A-F][0-9A-F][0-9A-F][0-9A-F]:' \
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F]:' \
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F].' \
                  '[0-9A-F][0-9A-F][0-9A-F][0-9A-F]'
            for ent in glob.glob(os.path.join(prefix + usb_name, pat)):
                ent = os.path.split(ent)[-1]
                dev_info.append(USBInfo.add_drv(os.path.join(prefix + usb_name, ent), "hidraw"))
                add = USBInfo.add_drv(os.path.join(prefix + usb_name, ent), "input")
                if add:
                    dev_info.append(add)
                else:
                    for ent2 in glob.glob(os.path.join(prefix + usb_name, ent + pat)):
                        ent2 = os.path.split(ent2)[-1]
                        dev_info.append(USBInfo.add_drv(os.path.join(prefix + usb_name, ent, ent2), "input"))
        return ''.join(dev_info)


class USBDevice(UserDict):
    usb_type = {
        '00': 'Device',
        '01': 'Audio',
        '02': 'Communications and CDC Control',
        '03': 'HID (Human Interface Device)',
        '05': 'Physical',
        '06': 'Image',
        '07': 'Printer',
        '08': 'Mass Storage',
        '09': 'Hub',
        '0a': 'CDC-Data',
        '0b': 'Smart Card',
        '0d': 'Content Security',
        '0e': 'Video',
        '0f': 'Personal Healthcare',
        '10': 'Audio / Video Devices',
        '11': 'Billboard Device Class',
        '12': 'USB Type - C Bridge Class',
        'dc': 'Diagnostic Device',
        'e0': 'Wireless Controller',
        'ef': 'Miscellaneous ',
        'fe': 'Application Specific',
        'ff': 'Vendor Specific',
        '-1': 'unk. '
    }

    def __init__(self, dev_path: str, show_all=False, *args, **kwargs):
        super(USBDevice, self).__init__(*args, **kwargs)
        self._show_all = show_all
        self._u_info = USBInfo()
        self._path = dev_path
        self._device_attr()

    def __getattr__(self, item):
        return self.get(item, '')

    def _device_attr(self):
        """'
        bDeviceClass,设备类别
        bDeviceSubClass,子类别
        bDeviceProtocol, 协议
        idVendor,  设备id
        idProduct,  产品id
        manufacturer,  品牌
        product,   设备名
        serial,  串行
        version,  usb2 or usb3
        speed,  速率Mbps
        bMaxPower,  电流
        maxchild, port数量
        bNumInterfaces 设备支持的接口总数
        """

        self.__setitem__('bDeviceClass', int(self.read_attr('bDeviceClass'), 16))
        self.__setitem__('bDeviceSubClass', int(self.read_attr('bDeviceSubClass'), 16))
        self.__setitem__('bDeviceProtocol', int(self.read_attr('bDeviceProtocol'), 16))
        self.__setitem__('idProduct', '0x' + self.read_attr('idProduct'))
        self.__setitem__('idVendor', '0x' + self.read_attr('idVendor'))
        self.__setitem__('manufacturer', self.read_attr('manufacturer'))
        self.__setitem__('product', self.read_attr('product'))
        self.__setitem__('serial', self.read_attr('serial'))
        self.__setitem__('version', self.read_attr('version'))
        self.__setitem__('speed', self.read_attr('speed'))
        self.__setitem__('bMaxPower', self.read_attr('bMaxPower'))
        self.__setitem__('maxchild', self.read_attr('maxchild'))
        self.__setitem__('bNumInterfaces', int(self.read_attr('bNumInterfaces')))
        self.__setitem__('type', USBDevice.usb_type.get('{:02x}'.format(self.bDeviceClass), 'unk'))
        self.__setitem__('name', self.manufacturer + self.product)
        self.__setitem__('driver', self.read_driver(self._path))
        new_name = self._u_info.find_usb_prod(self.idVendor, self.idProduct)
        if new_name:
            self.__setitem__('name', new_name)
        dev_name = USBInfo.find_dev(self.driver, self._path)
        if not dev_name:
            dev_name = os.path.split(self._path)[-1]
        self.__setitem__('dev_name', dev_name)
        bus_id = self.read_attr('busnum')
        dev_id = self.read_attr('devnum')
        self.__setitem__('bus_id', bus_id if bus_id else '-')
        self.__setitem__('dev_id', dev_id if dev_id else '-')
        self.__setitem__('endpoint', self._end_point_attr(os.path.join(self._path, 'ep_00')))
        self.get_interface()

    def _get_end_point_attr(self, interface_path: str) -> list:
        end_point = []
        for end_point_path in glob.glob(os.path.join(interface_path, 'ep_*')):
            end_point.append(self._end_point_attr(end_point_path))
        return end_point

    def _end_point_attr(self, end_point_path: str) -> dict:
        bInterval = int(self.read_attr("bInterval", end_point_path), 16)
        return {
            'name': os.path.split(end_point_path)[-1],
            'bEndpointAddress': int(self.read_attr('bEndpointAddress', end_point_path), 16),
            'bInterval': bInterval,
            'bLength': int(self.read_attr('bLength', end_point_path), 16),
            'type': self.read_attr('type', end_point_path),
            'bmAttributes': int(self.read_attr('bmAttributes', end_point_path), 16),
            'wMaxPacketSize': int(self.read_attr('wMaxPacketSize', end_point_path), 16)
        }

    def get_interface(self) -> None:
        interface_path = glob.glob(self._path + '/*:[0-9].[0-9]')
        interfaces = []
        for _interface in interface_path:
            interface = self._interface_attr(_interface)
            interface['end_points'] = self._get_end_point_attr(_interface)
            interfaces.append(interface)
        self.__setitem__('interfaces', interfaces)

    def _interface_attr(self, interface_path: str):
        _interface_attr = ['bInterfaceClass',
                           'bInterfaceSubClass',
                           'bInterfaceProtocol',
                           'bNumEndpoints']
        bInterfaceClass = int(self.read_attr('bInterfaceClass', interface_path), 16)
        bInterfaceSubClass = int(self.read_attr('bInterfaceSubClass', interface_path), 16)
        bInterfaceProtocol = int(self.read_attr('bInterfaceProtocol', interface_path), 16)
        driver = self.read_driver(interface_path)
        _interface = {
            'bInterfaceClass': bInterfaceClass,
            'bInterfaceSubClass': bInterfaceSubClass,
            'bInterfaceProtocol': bInterfaceProtocol,
            'bNumEndpoints': int(self.read_attr('bNumEndpoints', interface_path)),
            'proto_name': self._u_info.find_usb_class(bInterfaceClass,
                                                      bInterfaceSubClass,
                                                      bInterfaceProtocol),
            'driver': driver,
            'dev_name': USBInfo.find_dev(driver, interface_path),
            'name': os.path.split(interface_path)[-1]
        }
        return _interface

    def read_attr(self, name: str, path=None):
        if path is None:
            path = os.path.join(self._path, name)
        else:
            path = os.path.join(path, name)
        if not os.path.exists(path):
            return '0'
        with open(path)as fp:
            attr = fp.readline().strip()
        if attr == '':
            return '0'
        return attr

    @staticmethod
    def read_driver(path: str) -> str:
        driver_path = os.path.join(path, 'driver')
        if os.path.exists(driver_path):
            return os.path.basename(os.readlink(driver_path))
        return ''

    def _repr_interface(self, interface: dict) -> str:
        body = "{} (IF) {:02x}:{:02x}:{:02x} {:+d}EP{} <{} {}>" \
            .format(interface['name'],
                    interface.get('bInterfaceClass'),
                    interface.get('bInterfaceSubClass'),
                    interface.get('bInterfaceProtocol'),
                    interface.get('bNumEndpoints'),
                    "" if interface.get('bNumEndpoints', 0) == 1 else "s",
                    interface.get('proto_name'),
                    interface.get('driver'),
                    interface.get('dev_name'))
        e_body = ''
        for end_point in interface['end_points']:
            e_body += self._repr_end_point(end_point, '\n\t|__ ')
        return body + e_body

    def _repr_end_point(self, end_point, level='\n|__ '):
        if not self._show_all:
            return ''
        e_body = '{}{} (EP) {:02x}:{} {} attr {:02x} len {:02x} max {:03x}'. \
            format(level,
                   end_point.get('name'),
                   end_point.get('bEndpointAddress'),
                   end_point.get('type'),
                   end_point.get('bInterval'),
                   end_point.get('bmAttributes'),
                   end_point.get('bLength'),
                   end_point.get('wMaxPacketSize'))
        return e_body

    def __str__(self) -> str:
        body = "{} {} {:02x} {:+2d}IFs [USB {}, {} Mbps, {}] ({}) {}".format(
            self.dev_name,
            "{}:{}".format(self.idVendor, self.idProduct),
            self.bDeviceClass,
            self.bNumInterfaces,
            self.version,
            self.speed,
            self.bMaxPower,
            self.name,
            self.type)

        i_body = ''
        for interface in self.interfaces:
            i_body += '\n|__ '
            i_body += self._repr_interface(interface)
        return body + self._repr_end_point(self.endpoint) + i_body

    def __repr__(self):
        return '<UsbDevice [{}] {}> {}:{} '.format(self.name,
                                                   self.type,
                                                   self.idVendor,
                                                   self.idProduct)


def find_usb():
    prefix = '/sys/bus/usb/devices'
    root_hub = 'usb*'
    usb_device = '[1-9]-[1-9]'
    usb_devices = []
    for root in glob.glob(os.path.join(prefix, root_hub)):
        usb_devices.append(root)
        child_usb = glob.glob(os.path.join(root, usb_device))
        usb_devices.extend(child_usb)
    return usb_devices


def list_usb(end_point=False, simple=False, json=False):
    for usb in find_usb():
        u = USBDevice(usb, end_point)
        if json:
            pprint.pprint(u.data)
            print('\n')
        elif simple:
            print(u.__repr__())
        else:
            print(u)


if __name__ == '__main__':
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    e, s, j = False, False, False
    if arg == '-s':
        s = True
    elif arg == '-j':
        j = True
    elif arg == '-e':
        e = True
    elif arg == '-h':
        print('Usage:\n\t-s  simple\n\t-j  json\n\t-e  show endpoint\n\t-h  show this')
        sys.exit(0)
    list_usb(e, s, j)
