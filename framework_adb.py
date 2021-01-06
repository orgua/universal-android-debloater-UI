import time
import sys
import os.path
from typing import NoReturn

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb, AdbDevice
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
from adb_shell.exceptions import UsbDeviceNotFoundError, DevicePathInvalidError

from framework_misc import save_to_log
from configuration import *

# ###############################################################################
#                                ADB                                            #
# ###############################################################################

# TODO: tcp-version - AdbDeviceTcp('192.168.0.222', 5555, default_transport_timeout_s=9.)


def connect_device_usb(key_file_path: str) -> AdbDevice:
    if not os.path.exists(key_file_path):
        keygen(key_file_path)
        print(f"-> generated and stored a new adb-RSA-key (was missing)")

    with open(key_file_path) as f:
        priv = f.read()
    with open(key_file_path + '.pub') as f:
        pub = f.read()
    signer = PythonRSASigner(pub, priv)
    try:
        _device = AdbDeviceUsb()  # TODO: there can be more than one phone, determine with "available", "list" or similar
    except UsbDeviceNotFoundError:
        _device = None
        print(f"ERROR: is device connected and ADB activated?")
    except DevicePathInvalidError:
        _device = None
        print("ERROR: Installation seems incomplete, adb-shell[usb] is missing (or not working as intended) or adb-server is still running on your system")
    if _device is not None:
        _device.connect(rsa_keys=[signer], auth_timeout_s=30)
    # time.sleep(adb_sleep)
    if check_device_availability(_device):
        print(f"-> connected to device per USB")
    return _device


def check_device_availability(_device: AdbDevice) -> bool:
    if _device is None:
        return False
    is_available = _device.available
    # time.sleep(adb_sleep)
    # TODO: add additional avail test with: try catch for int(_device.shell("getprop ro.build.version.sdk").strip("\n\r")) > 0
    if not is_available:
        sys.exit("Error while connecting to device")
    return is_available


def pull_file_from_device(_device: AdbDevice, _remote_file_path: str, _local_file_path: str) -> int:
    if not check_device_availability(_device):
        return 0
    mode, size, mtime = _device.stat(_remote_file_path)
    if size > 0:
        _device.pull(_remote_file_path, _local_file_path)
        print(f"-> pulled file '{_remote_file_path}' from device, size = {size} byte")
        # time.sleep(adb_sleep)
    else:
        print(f"-> failed pulling file = '{_remote_file_path}'")
    return size


def push_device_package_list_backup(_device: AdbDevice, _local_file_path: str, _remote_file_path: str) -> NoReturn:
    if not os.path.exists(_local_file_path) or not check_device_availability(_device):
        return
    _device.push(_local_file_path, _remote_file_path)
    # time.sleep(adb_sleep)
    print(f"-> pushed file to device, file = '{_remote_file_path}'")


def restore_device_package_list(_device: AdbDevice) -> pd.DataFrame:
    global remote_package_file_path, local_backup_package_file_path
    size = pull_file_from_device(_device, remote_package_file_path, local_backup_package_file_path)
    if size > 0:
        # TODO: refactor to proper fn with try catch, used at least 3x
        return pd.read_csv(local_backup_package_file_path, sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    else:
        return pd.DataFrame(columns=package_columns + debloat_columns[1:3])


def backup_device_package_list(_device: AdbDevice, packages: pd.DataFrame) -> bool:
    global package_columns, debloat_columns, csv_decimal, csv_delimiter, csv_encoding
    global local_backup_package_file_path, remote_package_file_path
    packages_filtered = packages[package_columns + debloat_columns[1:3]]
    packages_filtered.to_csv(local_backup_package_file_path, sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    push_device_package_list_backup(_device, local_backup_package_file_path, remote_package_file_path)
    return True


def get_device_properties(_device: AdbDevice) -> int:
    global device_name, device_android_version, device_android_sdk
    if not check_device_availability(_device):
        return 0
    device_name = _device.shell("getprop ro.product.manufacturer").strip("\n\r") + " " + _device.shell("getprop ro.product.device").strip("\n\r")
    device_android_version = _device.shell("getprop ro.build.version.release").strip("\n\r")
    device_android_sdk = int(_device.shell("getprop ro.build.version.sdk").strip("\n\r"))
    print(f"-> read device properties, got device='{device_name}' with android {device_android_version}, sdk={device_android_sdk}")
    return device_android_sdk


def get_device_users(_device: AdbDevice) -> pd.DataFrame:
    user_columns = ["index", "name", "unknown"]
    if not check_device_availability(_device):
        return pd.DataFrame(columns=user_columns)
    response = _device.shell("pm list users")
    # time.sleep(adb_sleep)
    user_list = list([])
    for line in response.splitlines():
        if not "UserInfo{" in line:
            continue
        if not "} running" in line:
            continue
        start = line.find("{") + 1
        end = line.find("}")
        user_list.append(pd.DataFrame([line[start:end].split(":")], columns=user_columns))
    print(f"-> read user lists, got {len(user_list)} entries")
    if len(user_list) > 0:
        user_df = pd.concat(user_list, ignore_index=True).sort_values(by="index", ascending=True).reset_index(drop=True)
    else:
        user_df = pd.DataFrame(columns=user_columns)
    return user_df


def read_package_list(_device: AdbDevice) -> pd.DataFrame:
    global package_options, package_list_query, package_option_names
    # TODO: vary query by android version
    if not check_device_availability(_device):
        return pd.DataFrame(columns=package_columns + debloat_columns)
    data = pd.DataFrame(columns=package_option_names)
    for option in package_options:
        opt_name = option[1]
        response = _device.shell(package_list_query + option[0])
        # time.sleep(adb_sleep)
        for line in response.splitlines():
            if line[0:8].lower() != "package:":
                continue
            package = line[8:]
            data.loc[package, opt_name] = True
    data = data.fillna(False)
    data.index.name = "package"
    data = data.sort_index().reset_index()
    # reformat for more usable meta-data: system package | 3rd-party (user), enabled | disabled, installed | uninstalled
    data.loc[:, "type"] = (data["sys_EN_pUninst"] | data["sys_DIS_pUninst"])  # True == System
    data.loc[:, "enabled"] = data["sys_EN_pUninst"] | data["3rd_EN_pUninst"]
    data.loc[:, "installed"] = data["sys_EN"] | data["sys_DIS"] | data["3rd_EN"] | data["3rd_DIS"]
    data.loc[:, "via_adb"] = True
    print(f"-> read package lists, got {len(data)} entries")
    return data[package_columns]


# adb halt, disable, uninstall program
def disable_package(_device: AdbDevice, package: str, _user: int, with_uninstall: bool = False) -> bool:
    global device_name, device_android_sdk
    if not check_device_availability(_device):
        return False
    # TODO: first find it, do nothing otherwise
    # sdk > 21 seems to need "--user 0"
    cmd_option = f"--user {_user}" if device_android_sdk > 21 else ""
    cmd1 = f"am force-stop {package}"
    cmd2 = f"pm disable-user {cmd_option} {package}"
    cmd3 = f"pm uninstall -k {cmd_option} {package}"  # "-k" implies to NOT delete user data
    cmd4 = f"pm clear {cmd_option} {package}"
    response1 = _device.shell(cmd1)
    # TODO: it could be that "am stopservice" is the new one >= marshmellow/23, the other one <= jelly bean
    response2 = _device.shell(cmd2)
    print(f"-> stopping  package '{package}' with response '{response1}'")
    print(f"-> disabling package '{package}' with response '{response2}'")
    # save_to_log(device_name, package, cmd1, response1)  # disabled non-critical cmd to keep log clean
    save_to_log(device_name, package, cmd2, response2)
    time.sleep(adb_sleep)
    if with_uninstall:
        response3 = _device.shell(cmd3)
        print(f"-> uninstall package '{package}' with response '{response3}'")
        save_to_log(device_name, package, cmd3, response3)
        time.sleep(adb_sleep)
    response4 = _device.shell(cmd4)
    print(f"-> clear userdata of package '{package}' with response '{response4}'")
    save_to_log(device_name, package, cmd4, response4)
    return True


def enable_package(_device: AdbDevice, package: str, _user: int, with_install: bool = False) -> bool:
    if not check_device_availability(_device):
        return False
    cmd1 = f"cmd package install-existing {package}"
    cmd2 = f"pm enable {package}"
    cmd3 = f"am startservice {package}"
    # TODO: sdk26+ requires services in the foreground "am start-foreground-service"
    if with_install:
        response1 = _device.shell(cmd1)
        print(f"-> install package '{package}' with response '{response1}'")
        save_to_log(device_name, package, cmd1, response1)
        time.sleep(adb_sleep)
    response2 = _device.shell(cmd2)
    response3 = _device.shell(cmd3)
    print(f"-> enabling package '{package}' with response '{response2}'")
    print(f"-> starting package '{package}' with response '{response3}'")
    save_to_log(device_name, package, cmd2, response2)
    # save_to_log(cmd3, device_name, response3)  # disabled non-critical cmd to keep log clean
    time.sleep(adb_sleep)
    return True


# TODO: backup current phone
# adb backup -apk -all -system -f "${PHONE:-phone}-`date +%Y%m%d-%H%M%S`.adb"

# TODO: store database on device

