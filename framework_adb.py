import time
import sys
import os.path
from typing import NoReturn

import pandas as pd
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb, AdbDevice
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
from adb_shell.exceptions import UsbDeviceNotFoundError, DevicePathInvalidError
from dearpygui.core import log_error, log_info

import framework_debloat as uad_fw
import framework_misc as misc
import configuration as cfg

# ###############################################################################
#                                ADB Globals                                    #
# ###############################################################################

pd.set_option('mode.chained_assignment', None)

device: AdbDevice = None
device_name: str = None
device_android_version = 0
device_android_sdk = 0
device_user: int = 0
device_is_connected: bool = False
device_packages: pd.DataFrame = pd.DataFrame(columns=cfg.package_columns + cfg.debloat_columns)

# ###############################################################################
#                                ADB                                            #
# ###############################################################################

# TODO: tcp-version - AdbDeviceTcp('192.168.0.222', 5555, default_transport_timeout_s=9.)


def connect_device_usb() -> NoReturn:
    global device, device_is_connected, device_name, device_android_version, device_user
    if not os.path.exists(cfg.adb_key_file_path):
        keygen(cfg.adb_key_file_path)
        log_info(f"[ADB] generated and stored a new adb-RSA-key (was missing)", logger="debuglog")

    with open(cfg.adb_key_file_path) as f:
        priv = f.read()
    with open(cfg.adb_key_file_path + '.pub') as f:
        pub = f.read()
    signer = PythonRSASigner(pub, priv)
    try:
        device = AdbDeviceUsb()  # TODO: there can be more than one phone, determine with "available", "list" or similar
    except UsbDeviceNotFoundError:
        device = None
        log_error(f"[ADB] is the device connected and ADB activated on device?", logger="debuglog")
    except DevicePathInvalidError:
        device = None
        log_error("[ADB] installation seems incomplete, adb-shell[usb] is missing (or not working as intended) or adb-server is still running on your system", logger="debuglog")
    if device is not None:
        device.connect(rsa_keys=[signer], auth_timeout_s=30)
    if not is_device_available():
        return
    device_is_connected = True
    log_info(f"[ADB] connected to USB-Device", logger="debuglog")
    update_device_properties()


def disconnect_device() -> NoReturn:
    global device_is_connected, device, device_packages
    device.close()
    device = None
    device_packages = pd.DataFrame(columns=cfg.package_columns + cfg.debloat_columns)
    device_is_connected = False
    log_info(f"[ADB] disconnected from Device", logger="debuglog")


def is_device_available() -> bool:
    global device
    if device is None:
        return False
    is_available = device.available
    # TODO: add additional avail test with: try catch for int(_device.shell("getprop ro.build.version.sdk").strip("\n\r")) > 0
    return is_available


def pull_file_from_device(_remote_file_path: str, _local_file_path: str) -> int:
    global device
    if not is_device_available():
        return 0
    mode, size, mtime = device.stat(_remote_file_path)
    if size > 0:
        device.pull(_remote_file_path, _local_file_path)
        log_info(f"[ADB] pulled file '{_remote_file_path}' from device, size = {size} byte", logger="debuglog")
    else:
        log_error(f"[ADB] failed pulling file ({_remote_file_path})", logger="debuglog")
    return size


def push_device_package_list_backup(_local_file_path: str, _remote_file_path: str) -> bool:
    global device
    if not os.path.exists(_local_file_path) or not is_device_available():
        return False
    device.push(_local_file_path, _remote_file_path)
    log_info(f"[ADB] pushed file to device ({_remote_file_path})", logger="debuglog")
    mode, size, mtime = device.stat(_remote_file_path)
    return size > 0


def restore_device_package_list() -> pd.DataFrame:
    size = pull_file_from_device(cfg.remote_package_file_path, cfg.local_backup_package_file_path)
    if size > 0:
        return misc.load_dataframe(cfg.local_backup_package_file_path)
    else:
        return pd.DataFrame(columns=cfg.package_columns + cfg.debloat_columns[1:3])


def backup_device_package_list() -> bool:
    global device_packages
    packages_filtered = device_packages[cfg.package_columns + cfg.debloat_columns[1:3]]
    misc.save_dataframe(packages_filtered, cfg.local_backup_package_file_path)
    push_device_package_list_backup(cfg.local_backup_package_file_path, cfg.remote_package_file_path)
    return True


def update_device_properties() -> int:
    global device, device_name, device_android_sdk, device_android_version, device_user
    if not is_device_available():
        return 0
    manufacturer = device.shell("getprop ro.product.manufacturer").strip("\n\r")
    product_name = device.shell("getprop ro.product.device").strip("\n\r")
    device_name = manufacturer + " " + product_name
    device_android_version = device.shell("getprop ro.build.version.release").strip("\n\r")
    device_android_sdk = int(device.shell("getprop ro.build.version.sdk").strip("\n\r"))
    log_info(f"[ADB] read device properties, '{device_name}', android {device_android_version}, sdk={device_android_sdk}", logger="debuglog")
    users = get_device_users()
    if len(users) > 1:
        log_info("[ADB] NOTE - there are several users, will choose first one in list!", logger="debuglog")
        log_info(str(users), logger="debuglog")
    device_user = users["index"].iloc[0]
    if device_android_sdk < 26:
        log_error("[ADB] Your android version is old (< 8.0).", logger="debuglog")
        log_error("[ADB] Uninstalled packages can't be restored.", logger="debuglog")
        log_error("[ADB] The GUI won't stop you from doing so.", logger="debuglog")
    return device_android_sdk


def get_device_users() -> pd.DataFrame:
    global device
    user_columns = ["index", "name", "unknown"]
    if not is_device_available():
        return pd.DataFrame(columns=user_columns)
    response = device.shell("pm list users")
    user_list = list([])
    for line in response.splitlines():
        if "UserInfo{" not in line:
            continue
        if "} running" not in line:
            continue
        start = line.find("{") + 1
        end = line.find("}")
        user_list.append(pd.DataFrame([line[start:end].split(":")], columns=user_columns))
    log_info(f"[ADB] read user list ({len(user_list)} entries)", logger="debuglog")
    if len(user_list) > 0:
        user_df = pd.concat(user_list, ignore_index=True).sort_values(by="index", ascending=True).reset_index(drop=True)
    else:
        user_df = pd.DataFrame(columns=user_columns)
    return user_df


def update_package_data() -> NoReturn:
    global device_packages
    package_data1 = device_packages if (len(device_packages) > 0) else restore_device_package_list()
    package_data1["via_adb"] = False
    package_data2 = read_package_data()
    package_data3 = pd.concat([package_data1, package_data2], ignore_index=True)
    package_data4 = package_data3.sort_values(by="via_adb", ascending=False).groupby("package").first().reset_index()
    device_packages = uad_fw.enrich_package_list(package_data4)
    log_info(f"[ADB] read package list ("
             f"{len(device_packages)} entries, "
             f"{len(device_packages[device_packages['via_adb'] == False])} via backup / not ADB)",
             logger="debuglog")


def read_package_data() -> pd.DataFrame:
    global device
    # TODO: vary query by android version
    if not is_device_available():
        return pd.DataFrame(columns=cfg.package_columns + cfg.debloat_columns)
    data = pd.DataFrame(columns=cfg.package_option_names)
    for option in cfg.package_options:
        opt_name = option[1]
        response = device.shell(cfg.package_list_query + option[0])
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
    return data[cfg.package_columns]


# adb halt, disable, uninstall program
def disable_package(package: str, with_uninstall: bool = False) -> bool:
    global device, device_user, device_android_sdk, device_name, device_packages
    if not is_device_available():
        return False
    # TODO: first find it, do nothing otherwise
    # sdk > 21 seems to need "--user 0"
    cmd_option = f"--user {device_user}" if device_android_sdk > 21 else ""
    # TODO: it could be that "am stopservice" is the new one >= marshmellow/23, the other one <= jelly bean
    cmd1 = f"am force-stop {package}"
    cmd2 = f"pm disable-user {cmd_option} {package}"
    cmd3 = f"pm uninstall -k {cmd_option} {package}"  # "-k" implies to NOT delete user data
    cmd4 = f"pm clear {cmd_option} {package}"
    response1 = device.shell(cmd1)
    response2 = device.shell(cmd2)
    print(f"-> stopped  package '{package}' with response '{response1}'")
    print(f"-> disabled package '{package}' with response '{response2}'")
    misc.save_to_log(device_name, package, cmd2, response2)
    device_packages.loc[device_packages["package"] == package, "enabled"] = False
    time.sleep(cfg.adb_sleep_time_s)
    if with_uninstall:
        response3 = device.shell(cmd3)
        time.sleep(cfg.adb_sleep_time_s)
        response4 = device.shell(cmd4)
        print(f"-> uninstalled package '{package}' with response '{response3}'")
        print(f"-> cleared userdata of package '{package}' with response '{response4}'")
        misc.save_to_log(device_name, package, cmd3, response3)
        misc.save_to_log(device_name, package, cmd4, response4)
        device_packages.loc[device_packages["package"] == package, "installed"] = False
    return True


def enable_package(package: str, with_install: bool = False) -> bool:
    global device, device_name, device_packages
    if not is_device_available():
        return False
    cmd1 = f"cmd package install-existing {package}"
    cmd2 = f"pm enable {package}"
    cmd3 = f"am startservice {package}"
    # TODO: sdk26+ requires services in the foreground "am start-foreground-service"
    if with_install:
        response1 = device.shell(cmd1)
        print(f"-> installed package '{package}' with response '{response1}'")
        misc.save_to_log(device_name, package, cmd1, response1)
        device_packages.loc[device_packages["package"] == package, "installed"] = True
        time.sleep(cfg.adb_sleep_time_s)
    response2 = device.shell(cmd2)
    response3 = device.shell(cmd3)
    print(f"-> enabled package '{package}' with response '{response2}'")  # TODO: parse and process response
    print(f"-> started package '{package}' with response '{response3}'")
    misc.save_to_log(device_name, package, cmd2, response2)
    device_packages.loc[device_packages["package"] == package, "enabled"] = True
    time.sleep(cfg.adb_sleep_time_s)
    return True


def clear_userdata_of_package(package: str) -> NoReturn:
    global device_user, device_android_sdk, device, device_name
    cmd_option = f"--user {device_user}" if device_android_sdk > 21 else ""
    # TODO: it could be that "am stopservice" is the new one >= marshmellow/23, the other one <= jelly bean
    cmd1 = f"am force-stop {package}"
    cmd4 = f"pm clear {cmd_option} {package}"
    response1 = device.shell(cmd1)
    response4 = device.shell(cmd4)
    misc.save_to_log(device_name, package, cmd4, response4)
    print(f"-> stopped package '{package}' with response '{response1}'")
    print(f"-> cleared userdata of package '{package}' with response '{response4}'")
    time.sleep(cfg.adb_sleep_time_s)


# TODO: backup current phone, there seems to be
# adb backup -apk -all -system -f "${PHONE:-phone}-`date +%Y%m%d-%H%M%S`.adb"
