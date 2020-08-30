import fcntl
import socket
import ctypes
import collections
import errno

ETH_GSTRING_LEN = 32
SCHAR_MAX = 127
ETHTOOL_LINK_MODE_MASK_MAX_KERNEL_NU32 = SCHAR_MAX
SOPASS_MAX = 6
IFNAMSIZ = 16
SIOCETHTOOL = 0x8946
ETH_SS_FEATURES = 4
ETHTOOL_GSSET_INFO = 0x37
ETHTOOL_GSTRINGS = 0x0000001b
ETHTOOL_GLINKSETTINGS = 0x0000004c
ETHTOOL_GCOALESCE = 0xe
ETHTOOL_GWOL = 0x00000005
ETHTOOL_GFEATURES = 0x0000003a
ETHTOOL_GLINK = 0x0000000a
SIOCGIFCONF = 0x8912  # TODO: get device
SIOCGIFHWADDR = 0x8927
SIOCGIFADDR	= 0x8915
SIOCGIFBRDADDR = 0x8919
SIOCGIFNETMASK = 0x891b

LMBTypePort = 0
LMBTypeMode = 1
LMBTypeOther = -1
LinkModeBit = collections.namedtuple('LinkModeBit', ('bit_index', 'name', 'type'))
LinkModeBits = (
    LinkModeBit(bit_index=0, name='10baseT/Half', type=LMBTypeMode),
    LinkModeBit(bit_index=1, name='10baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=2, name='100baseT/Half', type=LMBTypeMode),
    LinkModeBit(bit_index=3, name='100baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=4, name='1000baseT/Half', type=LMBTypeMode),
    LinkModeBit(bit_index=5, name='1000baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=6, name='Autoneg', type=LMBTypeOther),
    LinkModeBit(bit_index=7, name='TP', type=LMBTypePort),
    LinkModeBit(bit_index=8, name='AUI', type=LMBTypePort),
    LinkModeBit(bit_index=9, name='MII', type=LMBTypePort),
    LinkModeBit(bit_index=10, name='FIBRE', type=LMBTypePort),
    LinkModeBit(bit_index=11, name='BNC', type=LMBTypePort),
    LinkModeBit(bit_index=12, name='10000baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=13, name='Pause', type=LMBTypeOther),
    LinkModeBit(bit_index=14, name='Asym_Pause', type=LMBTypeOther),
    LinkModeBit(bit_index=15, name='2500baseX/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=16, name='Backplane', type=LMBTypeOther),
    LinkModeBit(bit_index=17, name='1000baseKX/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=18, name='10000baseKX4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=19, name='10000baseKR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=20, name='10000baseR_FEC', type=LMBTypeMode),
    LinkModeBit(bit_index=21, name='20000baseMLD2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=22, name='20000baseKR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=23, name='40000baseKR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=24, name='40000baseCR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=25, name='40000baseSR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=26, name='40000baseLR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=27, name='56000baseKR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=28, name='56000baseCR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=29, name='56000baseSR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=30, name='56000baseLR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=31, name='25000baseCR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=32, name='25000baseKR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=33, name='25000baseSR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=34, name='50000baseCR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=35, name='50000baseKR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=36, name='100000baseKR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=37, name='100000baseSR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=38, name='100000baseCR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=39, name='100000baseLR4_ER4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=40, name='50000baseSR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=41, name='1000baseX/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=42, name='10000baseCR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=43, name='10000baseSR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=44, name='10000baseLR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=45, name='10000baseLRM/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=46, name='10000baseER/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=47, name='2500baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=48, name='5000baseT/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=49, name='FEC_NONE', type=LMBTypeOther),
    LinkModeBit(bit_index=50, name='FEC_RS', type=LMBTypeOther),
    LinkModeBit(bit_index=51, name='FEC_BASER', type=LMBTypeOther),
    LinkModeBit(bit_index=52, name='50000baseKR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=53, name='50000baseSR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=54, name='50000baseCR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=55, name='50000baseLR_ER_FR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=56, name='50000baseDR/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=57, name='100000baseKR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=58, name='100000baseSR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=59, name='100000baseCR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=60, name='100000baseLR2_ER2_FR2/Full',
                type=LMBTypeMode),
    LinkModeBit(bit_index=61, name='100000baseDR2/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=62, name='200000baseKR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=63, name='200000baseSR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=64, name='200000baseLR4_ER4_FR4/Full',
                type=LMBTypeMode),
    LinkModeBit(bit_index=65, name='200000baseDR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=66, name='200000baseCR4/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=67, name='100baseT1/Full', type=LMBTypeMode),
    LinkModeBit(bit_index=68, name='1000baseT1/Full', type=LMBTypeMode),
)
LinkModeBits_by_index = {bit.bit_index: bit for bit in LinkModeBits}


class Coalesce(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("rx_coalesce_usecs", ctypes.c_uint32),
        ("rx_max_coalesced_frames", ctypes.c_uint32),
        ("rx_coalesce_usecs_irq", ctypes.c_uint32),
        ("rx_max_coalesced_frames_irq", ctypes.c_uint32),
        ("tx_coalesce_usecs", ctypes.c_uint32),
        ("tx_max_coalesced_frames", ctypes.c_uint32),
        ("tx_coalesce_usecs_irq", ctypes.c_uint32),
        ("tx_max_coalesced_frames_irq", ctypes.c_uint32),
        ("stats_block_coalesce_usecs", ctypes.c_uint32),
        ("use_adaptive_rx_coalesce", ctypes.c_uint32),
        ("use_adaptive_tx_coalesce", ctypes.c_uint32),
        ("pkt_rate_low", ctypes.c_uint32),
        ("rx_coalesce_usecs_low", ctypes.c_uint32),
        ("rx_max_coalesced_frames_low", ctypes.c_uint32),
        ("tx_coalesce_usecs_low", ctypes.c_uint32),
        ("tx_max_coalesced_frames_low", ctypes.c_uint32),
        ("pkt_rate_high", ctypes.c_uint32),
        ("rx_coalesce_usecs_high", ctypes.c_uint32),
        ("rx_max_coalesced_frames_high", ctypes.c_uint32),
        ("tx_coalesce_usecs_high", ctypes.c_uint32),
        ("tx_max_coalesced_frames_high", ctypes.c_uint32),
        ("rate_sample_interval", ctypes.c_uint32),
    ]

    def items(self):
        data = {}
        for _field in self._fields_:
            data[_field[0]] = getattr(self, _field[0])
        return data


class SsetInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
        ("sset_mask", ctypes.c_uint64),
        ("data", ctypes.c_uint32),
    ]


class Gstrings(ctypes.Structure):
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("string_set", ctypes.c_uint32),
        ("len", ctypes.c_uint32),
        ("strings", ctypes.c_ubyte * ETH_GSTRING_LEN * 256)
    ]


class GetFeaturesBlock(ctypes.Structure):
    _fields_ = [
        ("available", ctypes.c_uint32),
        ("requested", ctypes.c_uint32),
        ("active", ctypes.c_uint32),
        ("never_changed", ctypes.c_uint32),
    ]


def bits_to_blocks(n_bits):
    return int((n_bits + 32 - 1) / 32)


class Gfeatures(ctypes.Structure):

    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("features", GetFeaturesBlock * bits_to_blocks(256)),
    ]


class LinkSettings(ctypes.Structure):
    INT32MINUS_UINT32 = ctypes.c_uint32(-1).value
    INT16MINUS_UINT16 = ctypes.c_uint16(-1).value
    LINK_DUPLEX_NAMES = {
        0x0: "Half",
        0x1: "Full",
        0xff: "Unknown"
    }
    LINK_PORT_NAMES = {
        0x00: "Twisted Pair",
        0x01: "AUI",
        0x02: "MII",
        0x03: "FIBRE",
        0x04: "BNC",
        0x05: "Direct Attach Copper",
        0xef: "NONE",
        0xff: "Other",
    }
    LINK_TP_MDI_NAMES = {
        0x01: "off",
        0x02: "on",
        0x03: "auto",
    }
    LINK_TRANSCEIVER_NAMES = {
        0x00: "Internal",
        0x01: "External",
    }
    _pack_ = 1
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("speed", ctypes.c_uint32),
        ("duplex", ctypes.c_uint8),
        ("port", ctypes.c_uint8),
        ("phy_address", ctypes.c_uint8),
        ("autoneg", ctypes.c_uint8),
        ("mdio_support", ctypes.c_uint8),
        ("eth_tp_mdix", ctypes.c_uint8),
        ("eth_tp_mdix_ctrl", ctypes.c_uint8),
        ("link_mode_masks_nwords", ctypes.c_int8),
        ("transceiver", ctypes.c_uint8),
        ("reserved1", ctypes.c_uint8 * 3),
        ("reserved", ctypes.c_uint32 * 7),
        ("link_mode_data", ctypes.c_uint32 *
         (3 * ETHTOOL_LINK_MODE_MASK_MAX_KERNEL_NU32)),
    ]

    @staticmethod
    def get_link_mode_bits(map_bits):
        for bit in LinkModeBits:
            map_i = bit.bit_index // 32
            map_bit = bit.bit_index % 32
            if map_i >= len(map_bits):
                continue
            if map_bits[map_i] & (1 << map_bit):
                yield bit

    def items(self):
        map_supported = []
        map_advertising = []
        map_lp_advertising = []
        i = 0
        while i != self.link_mode_masks_nwords:
            map_supported.append(self.link_mode_data[i])
            i += 1
        while i != self.link_mode_masks_nwords * 2:
            map_advertising.append(self.link_mode_data[i])
            i += 1
        while i != self.link_mode_masks_nwords * 3:
            map_lp_advertising.append(self.link_mode_data[i])
            i += 1
        bits_supported = LinkSettings.get_link_mode_bits(map_supported)
        supported_ports = []
        supported_modes = []
        for bit in bits_supported:
            if bit.type == LMBTypePort:
                supported_ports.append(bit.name)
            elif bit.type == LMBTypeMode:
                supported_modes.append(bit.name)
        if self.speed in [0, self.INT32MINUS_UINT32, self.INT16MINUS_UINT16]:
            speed = 'Unknown'
        else:
            speed = self.speed
        duplex = self.LINK_DUPLEX_NAMES.get(self.duplex, None)

        keys = ['speed', 'duplex', 'autoneg', 'supported_ports', 'supported_modes',
                'port', 'phy_address', 'eth_tp_mdix', 'eth_tp_mdix_ctrl', 'transceiver']
        values = [speed, duplex, bool(self.autoneg), supported_ports, supported_modes,
                  self.LINK_PORT_NAMES.get(self.port, None), self.phy_address,
                  self.LINK_TP_MDI_NAMES.get(self.eth_tp_mdix, None),
                  self.LINK_TP_MDI_NAMES.get(self.eth_tp_mdix_ctrl, None),
                  self.LINK_TRANSCEIVER_NAMES.get(self.transceiver, None)
                  ]
        return dict(zip(keys, values))

    def __str__(self):
        strings = []
        for key, value in self.data().items():
            strings.append('{}: {}'.format(key, value))
        return '\n'.join(strings)


class WolInfo(ctypes.Structure):
    # Wake-On-Lan options.
    WAKE_PHY = (1 << 0)
    WAKE_UCAST = (1 << 1)
    WAKE_MCAST = (1 << 2)
    WAKE_BCAST = (1 << 3)
    WAKE_ARP = (1 << 4)
    WAKE_MAGIC = (1 << 5)
    WAKE_MAGICSECURE = (1 << 6)  # only meaningful if WAKE_MAGIC
    WAKE_FILTER = (1 << 7)
    WAKE_NAMES = {
        WAKE_PHY: "phy",
        WAKE_UCAST: "ucast",
        WAKE_MCAST: "mcast",
        WAKE_BCAST: "bcast",
        WAKE_ARP: "arp",
        WAKE_MAGIC: "magic",
        WAKE_MAGICSECURE: "magic_secure",
        WAKE_FILTER: "filter",
    }
    EthtoolBitsetBit = collections.namedtuple('EthtoolBitsetBit',
                                              ('index', 'name', 'enable', 'set'))
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("supported", ctypes.c_uint32),
        ("wolopts", ctypes.c_uint32),
        ("sopass", ctypes.c_uint8 * SOPASS_MAX),
    ]

    def items(self):
        dict_wol_modes = {}
        for bit_index, name in self.WAKE_NAMES.items():
            if self.supported & bit_index:
                dict_wol_modes[name] = self.EthtoolBitsetBit(
                    bit_index, name,
                    self.wolopts & bit_index != 0, set=None)
        return {'mode': dict_wol_modes, 'sopass': None}


class Linked(ctypes.Structure):
    """struct ethtool_value {
        __u32	cmd;
        __u32	data;
    };"""
    _fields_ = [
        ('cmd', ctypes.c_uint32),
        ('data', ctypes.c_uint32)
    ]

    @property
    def state(self):
        return bool(self.data)


class IfReqData(ctypes.Union):
    _fields_ = [
        ('linked', ctypes.POINTER(Linked)),
        ("coalesce", ctypes.POINTER(Coalesce)),
        ("sset_info", ctypes.POINTER(SsetInfo)),
        ("gstrings", ctypes.POINTER(Gstrings)),
        ("gfeatures", ctypes.POINTER(Gfeatures)),
        ("glinksettings", ctypes.POINTER(LinkSettings)),
        ("wolinfo", ctypes.POINTER(WolInfo))
    ]


class IfReq(ctypes.Structure):
    _pack_ = 1
    _anonymous_ = ("u",)
    _fields_ = [
        ("ifr_name", ctypes.c_uint8 * IFNAMSIZ),
        ("u", IfReqData)
    ]


class Ifconfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('ifc_len', ctypes.c_int),
        ('ifc_buf', ctypes.POINTER(IfReq)),
    ]


class Ethtool(object):

    def __init__(self, name=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
        self.if_name = None
        self.if_req = None

        if name is not None:
            self._change_name(name)

    def _change_name(self, name):
        self.if_name = bytearray(name, 'utf-8')
        self.if_name.extend(b"\0" * (IFNAMSIZ - len(self.if_name)))
        self.if_req = IfReq()
        self.if_req.ifr_name = (ctypes.c_uint8 * IFNAMSIZ)(*self.if_name)

    def ioctl(self, command=SIOCETHTOOL):
        try:
            if fcntl.ioctl(self.sock, command, self.if_req):
                raise OSError('NotSupported: {}'.format(self.if_name.decode("utf-8")))
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                raise OSError('NotSupported: {}'.format(self.if_name.decode("utf-8")))
            elif e.errno == errno.ENODEV:
                raise OSError('NoSuchDevice: {}'.format(self.if_name.decode("utf-8")))
            raise

    def _get_stringset(self,
                       set_id=ETH_SS_FEATURES,
                       drvinfo_offset=0,
                       null_terminate=1):
        sset_info = SsetInfo(cmd=ETHTOOL_GSSET_INFO,
                             reserved=0,
                             sset_mask=1 << set_id)
        self.if_req.sset_info = ctypes.pointer(sset_info)
        fcntl.ioctl(self.sock, SIOCETHTOOL, self.if_req)
        if sset_info.sset_mask:
            length = sset_info.data
        else:
            length = 0

        strings_found = []
        gstrings = Gstrings(cmd=ETHTOOL_GSTRINGS,
                            string_set=set_id,
                            len=length)
        self.if_req.gstrings = ctypes.pointer(gstrings)
        self.ioctl()

        for i in range(length):
            buf = ''
            for j in range(ETH_GSTRING_LEN):
                code = gstrings.strings[i][j]
                if code == 0:
                    break
                buf += chr(code)
            strings_found.append(buf)
        return strings_found

    def get_features(self):
        stringsset = self._get_stringset()
        cmd = Gfeatures()
        cmd.cmd = ETHTOOL_GFEATURES
        cmd.size = bits_to_blocks(len(stringsset))
        try:
            self.if_req.gfeatures = ctypes.pointer(cmd)
            self.ioctl()
            data = {}
            for i, name in enumerate(stringsset):
                feature_i = i // 32
                flag_bit = 1 << (i % 32)
                data[name] = {'is_available': cmd.features[feature_i].available & flag_bit != 0,
                              'is_active': cmd.features[feature_i].active & flag_bit != 0,
                              'is_requested': cmd.features[feature_i].requested & flag_bit != 0,
                              'is_never_changed': cmd.features[feature_i].never_changed & flag_bit != 0}
            return data
        except OSError as error:
            print(error)
            return {}

    def get_link_settings(self):
        ecmd = LinkSettings()
        ecmd.cmd = ETHTOOL_GLINKSETTINGS
        self.if_req.glinksettings = ctypes.pointer(ecmd)
        try:
            self.ioctl()
            if ecmd.link_mode_masks_nwords >= 0 or \
                    ecmd.cmd != ETHTOOL_GLINKSETTINGS:
                raise Exception('NotSupported')
            ecmd.link_mode_masks_nwords = -ecmd.link_mode_masks_nwords
            self.ioctl()
            if ecmd.link_mode_masks_nwords <= 0 or \
                    ecmd.cmd != ETHTOOL_GLINKSETTINGS:
                raise Exception('NotSupported')
            return ecmd.items()
        except OSError as error:
            print(error)
            return {}

    def get_wol(self):
        cmd = WolInfo(cmd=ETHTOOL_GWOL)
        self.if_req.wolinfo = ctypes.pointer(cmd)
        try:
            self.ioctl()
            return cmd.items()
        except OSError as error:
            print(error)
            return {}

    def get_coalesce(self):
        cmd = Coalesce(cmd=ETHTOOL_GCOALESCE)
        self.if_req.coalesce = ctypes.pointer(cmd)
        try:
            self.ioctl()
            return cmd.items()
        except OSError as error:
            print(error)
            return {}

    def if_link(self):
        cmd = Linked(cmd=ETHTOOL_GLINK)
        self.if_req.linked = ctypes.pointer(cmd)
        try:
            self.ioctl()
            return cmd.state
        except OSError as error:
            print(error)
            return {}

    @property
    def info(self):
        data = {}
        self.ioctl(SIOCGIFHWADDR)
        data['mac'] = ':'.join(['{:x}'.format(m) for m in bytearray(self.if_req.u)[2:8]])
        try:
            self.ioctl(SIOCGIFADDR)
            data['ip'] = '.'.join(['{}'.format(m) for m in bytearray(self.if_req.u)[4:8]])
        except OSError as error:
            if error.errno == errno.EADDRNOTAVAIL:
                data['ip'] = ''
        try:
            self.ioctl(SIOCGIFBRDADDR)
            data['brd'] = '.'.join(['{}'.format(m) for m in bytearray(self.if_req.u)[4:8]])
        except OSError as error:
            if error.errno == errno.EADDRNOTAVAIL:
                data['brd'] = ''
        try:
            self.ioctl(SIOCGIFNETMASK)
            data['mask'] = '.'.join(['{}'.format(m) for m in bytearray(self.if_req.u)[4:8]])
        except OSError as error:
            if error.errno == errno.EADDRNOTAVAIL:
                data['mask'] = ''
        return data


if __name__ == '__main__':
    inc = Ethtool('wlp2s0')
    print(inc.get_wol())
    print(inc.get_coalesce())
    print(inc.get_features())
    print(inc.get_link_settings())
    print(inc.if_link())
    print(inc.info)
