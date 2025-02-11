#!/usr/bin/env python3
import serial as ser
import pyudev
import logging
import sys
import os
import time
from pyroute2 import IPRoute, NetNS, netns
import can


#add colours to text
class CustomFormatter(logging.Formatter): 

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;1m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[36;20m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: green + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record) 
    
# logger records to "print" for qt to read
class QtLoggerHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        print(log_entry)

def write_sysfs(path, value):
    try:
        with open(path, "w") as f:
            f.write(str(value))
        return 0
    except IOError as e:
        logger.error(f"[ERROR] Cannot write to {path}: {e}")
        return 1

def test_usb():
    context = pyudev.Context()
    usb_devices = [device for device in context.list_devices(subsystem='usb', DEVTYPE='usb_device')]
    usb_devices_count = len(usb_devices)
    if usb_devices_count == 10:
        logger.info('[OK] USB OK')
        return 0
    else:
        logger.error(f'[ERROR] total USB device count must be 8, but there are {usb_devices_count}')
        return 1

def test_pci():
    PCI_DIR_PATH = '/sys/bus/pci/devices'
    pci_devices_count = len(os.listdir(PCI_DIR_PATH))
    if pci_devices_count == 2:
        logger.info('[OK] MCPIE connector PCIE lines: OK')
        return 0
    else:
        logger.error(f'[ERROR] MPCIE connector PCIE lines error ({pci_devices_count} visible)')
        return 1
    

# UART1 and UART2 cross connect test
# UART3(X10_RA) lopback test
def test_uart(mode = "single"): 
    ret = 0
    with ser.Serial('/dev/ttyS5', 115200, timeout=2, rtscts=1) as uart1, ser.Serial('/dev/ttyS4', 115200, timeout=2, rtscts=1) as uart2, ser.Serial('/dev/ttyS0') as uart3:
        while(True):
            uart1.write(b'tst_ttyS5_ttyS4\n') 
            res = uart2.readline()
            
            if res == b'tst_ttyS5_ttyS4\n':
                logger.info("[OK] UART1(X10_RC) and UART2(X10_RB) cross connect 1->2: OK")
            else:
                logger.error(f"[ERROR] UART1(X10_RC) and UART2(X10_RB) cross connect 1->2 error, rcvd: {res}")
                ret = 1
            
            uart2.write(b'tst_ttyS4_ttyS5\n')
            res = uart1.readline()

            if res == b'tst_ttyS4_ttyS5\n':
                logger.info("[OK] UART2(X10_RB) and UART1(X10_RC) cross connect 2->1: OK")
            else:
                logger.error(f"[ERROR] UART2(X10_RB) and UART1(X10_RC) cross connect 2->1 error, rcvd: {res}")
                ret = 1

            uart3.write(b'tst_ttyS8_tst\n')
            res = uart3.readline()

            if res == b'tst_ttyS8_tst\n':
                logger.info("[OK] UART3(X10_RA): OK")
            else:
                logger.error(f"[ERROR] UART3(X10_RA) loopback error, rcvd: {res}")
                ret = 1

            time.sleep(0.5)
            if mode == "single":
                break;        
    return ret


def test_rtc():
    time.clock_settime(time.CLOCK_REALTIME, 1736853697)
    os.system('hwclock -w -u')
    t1 = os.popen('hwclock').read()
    time.sleep(1)
    t2 = os.popen('hwclock').read()
    if t1 != t2:
        logger.info("[OK] RTC tick: OK")
        return 0
    else:
        logger.error("[ERROR] RTC time not ticking!")
        return 1

def test_hdmi():
    try:
      f = open("/sys/class/drm/card0-HDMI-A-1/status")
      logger.debug("File 'status' opened successfully")
    except IOError:
      logger.error("[ERROR] HDMI file 'status' does not appear to exist.")
      return 1
    
    status = f.read().replace('\n', '')
    f.close()
    if(status ==  "connected"):
        logger.info("[OK] HDMI: OK")
        return 0
    else:
        logger.error(f"[ERROR] HDMI is not connected, state: {status}")
        return 1

def test_serial_communication(tx_serial, rx_serial, message):
    tx_serial.write(message.encode())
    time.sleep(0.1)
    received = rx_serial.read(len(message)).decode()
    if received == message:
        logger.info(f"[OK] RS422 {tx_serial.port} -> {rx_serial.port}: OK")
        return 0
    else:
        logger.error(f"[ERROR] RS422 {tx_serial.port} -> {rx_serial.port} error, received: {received}")
        return 1

def test_rs422():
    ret = 0
    ret += write_sysfs("/sys/class/leds/rs_A_fullduplex_mode/brightness", 1)
    ret += write_sysfs("/sys/class/leds/rs_A_therm_AB/brightness", 1)
    ret += write_sysfs("/sys/class/leds/rs_A_therm_XY/brightness", 1)
    ret += write_sysfs("/sys/class/leds/rs_B_fullduplex_mode/brightness", 1)
    ret += write_sysfs("/sys/class/leds/rs_B_therm_AB/brightness", 1)
    ret += write_sysfs("/sys/class/leds/rs_B_therm_XY/brightness", 1)
    if ret>0:
        return 1

    with ser.Serial("/dev/ttySC0", 115200, timeout=1, rtscts=False, dsrdtr=False) as serial0, ser.Serial("/dev/ttySC1", 115200, timeout=1, rtscts=False, dsrdtr=False)as serial1:
        ret += test_serial_communication(serial0, serial1, "t_ttySC0_ttySC1")
        ret += test_serial_communication(serial1, serial0, "t_ttySC1_ttySC0")
    
    if ret>0:
        return 1
    
    return 0

def test_sata():
    sataPath = '/sys/block'
    devPathList = [os.path.join(sataPath, fname) for fname in os.listdir(sataPath)]
    if any("fc400000.sata" in os.path.realpath(devPath) for devPath in devPathList):
        logger.info('[OK] SATA (M.2): OK')
        return 0
    else:
        logger.error('[ERROR] M.2 SATA not detected')
        return 1
    
def test_can():
    with open("/sys/class/leds/CAN_A_therm/brightness", 'w') as f:
        f.write("1\n")
    with open("/sys/class/leds/CAN_B_therm/brightness", 'w') as f:
        f.write("1\n")

    canfd_support = False
    canfd_file_path = "/proc/device-tree/can@fe590000/compatible"
    with open(canfd_file_path, "r") as f:
        if "rockchip,rk3568v2-canfd" in f.read():
            canfd_support = True
    
    message = can.Message(arbitration_id=0x500, data=[0x1E, 0x10, 0x10], is_extended_id=False)

    try:
        if canfd_support:
            with can.interface.Bus(channel='can0', interface='socketcan', bitrate=1000000, dbitrate=1000000, fd=True) as bus0, can.interface.Bus(channel='can1', interface='socketcan', bitrate=1000000, dbitrate=1000000, fd=True) as bus1: 
                bus1.send(message)
                recv_msg = bus0.recv(timeout=2)
                if recv_msg == None:
                    logger.error(f"[ERROR] No CANFD loopback, rcvd: None")
                    return 1       
                if recv_msg.data == b'\x1e\x10\x10':
                    logger.info(f"[OK] CANFD: OK")
                    return 0
            logger.error(f"[ERROR] No CANFD loopback, rcvd: {recv_msg.data}")
            return 1       
        else:
            with can.interface.Bus(channel='can0', interface='socketcan', bitrate=1000000) as bus0, can.interface.Bus(channel='can1', interface='socketcan', bitrate=1000000) as bus1:
                bus1.send(message)
                recv_msg = bus0.recv(timeout=2)
                if recv_msg == None:
                    logger.error(f"[ERROR] No CAN loopback, rcvd: None")
                if recv_msg.data == b'\x1e\x10\x10':
                    logger.info(f"[OK] CAN: OK")
                    return 0
            logger.error(f"[ERROR] No CAN loopback, rcvd: {recv_msg.data}")
            return 1
    except Exception as e:
        logger.error(f"[ERROR] Can't send/read from CAN interface: {e}")
        return 1

def test_emmc():
    if (os.path.exists('/dev/mmcblk0')):
        logger.info("[OK] EMMC detect: OK")
        return 0
    else:
        logger.error("[ERROR] EMMC not detected")
        return 1

def create_netns(name):
    if not os.path.exists(f"/var/run/netns/{name}"):
        netns.create(name)
        logger.debug(f"NetNS created: {name}")

def delete_netns(name):
    netns.remove(name)
    logger.debug(f"NetNS created: {name}")

def test_eth_loop(dev1="eth0", dev2="eth1"):
    ns_server_name = f"ns_server_{dev1}"
    ns_client_name = f"ns_client_{dev2}"
    ret = 0
    try:
        create_netns(ns_server_name)
        create_netns(ns_client_name)

        with IPRoute() as ipr:
            try:
                server_index = ipr.link_lookup(ifname=dev1)[0]
                client_index = ipr.link_lookup(ifname=dev2)[0]
                ipr.link("set", index=server_index, net_ns_fd=ns_server_name)
                ipr.link("set", index=client_index, net_ns_fd=ns_client_name)
                logger.debug(f"Interfaces {dev1} and {dev2} moved to netns")
            except IndexError:
                logger.error("[ERROR] One of interfaces in not present")
                ret = 1
                return 1

        with NetNS(ns_server_name) as ns_server:
            dev1_index = ns_server.link_lookup(ifname=dev1)[0]
            ns_server.addr("add", index=dev1_index, address="192.168.99.1", mask=24)
            ns_server.link("set", index=dev1_index, state="up")
            logger.debug(f"Server: interface {dev1} is configured, IP: 192.168.99.1/24")

        with NetNS(ns_client_name) as ns_client:
            dev2_index = ns_client.link_lookup(ifname=dev2)[0]
            ns_client.addr("add", index=dev2_index, address="192.168.99.2", mask=24)
            ns_client.link("set", index=dev2_index, state="up")

        pause = 3
        logger.debug(f"Waiting for {pause} sec. for settings to apply. (For 100Mbps ethernet wire - set 15 sec. For 1Gbps - 3 sec.)")
        time.sleep(pause)

        logger.debug(f"Ping {dev2} (192.168.99.2) -> 192.168.99.1")
        ping_result = os.system(f"ip netns exec {ns_client_name} ping -c 1 -w 3 192.168.99.1")

        if ping_result == 0:
            logger.info("[OK] Ethernet: OK")
            ret = 0
        else:
            logger.error("[ERROR] Ethernet loopback failed")
            ret = 1

    finally:
        delete_netns(ns_server_name)
        delete_netns(ns_client_name)
        return ret

def complex_test():
    ret = 0
    ret += test_usb()
    ret += test_pci()
    ret += test_hdmi()
    ret += test_uart()
    ret += test_rs422()
    ret += test_sata()
    ret += test_rtc()
    ret += test_can()
    ret += test_emmc()
    ret += test_eth_loop()
    if ret > 0:
        return 1
    return 0

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

isQtRequest = False
for arg in sys.argv:
    if arg == '-v':
        logger.setLevel(logging.DEBUG)
    if arg == '-q':
        isQtRequest = True


if isQtRequest:
    qtHandler = QtLoggerHandler()
    logger.addHandler(qtHandler)
else:
    colorHandler = logging.StreamHandler()
    colorHandler.setFormatter(CustomFormatter())
    logger.addHandler(colorHandler)
    

if len(sys.argv) >= 2:
    testOption = sys.argv[len(sys.argv)-1]
    logger.info(f'[START] {testOption} test started')
    if testOption == 'COMPLEX':
        ret = complex_test()  
    elif testOption == 'USB':
        ret = test_usb()
    elif testOption == 'PCI':
        ret = test_pci()
    elif testOption == 'HDMI':
        ret = test_hdmi()
    elif testOption == 'UART':
        ret = test_uart()
    elif testOption == 'UART_ENDLESS':
        ret = test_uart('endless')
    elif testOption == 'RS422':
        ret = test_rs422()
    elif testOption == 'SATA':
        ret = test_sata()
    elif testOption == 'RTC':
        ret = test_rtc()
    elif testOption == 'CAN':
        ret = test_can()
    elif testOption == 'EMMC':
        ret = test_emmc()
    elif testOption == 'ETHERNET':
        ret = test_eth_loop()
    else:
        ret = complex_test()
        
    if ret == 0:
        logger.warning(f'[SUCCESS] {testOption} test passed')
    else:
        logger.error(f'[FAIL] {testOption} test failed')
else:
    complex_test()
