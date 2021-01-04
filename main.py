# Devices to Test:
# s8 - alexis, https://forum.xda-developers.com/t/alexis-rom-9-1_dtj1_10-2020-patches-27-10-2020-ported-s10-stuffs-s9wallpapers.3753975/
# s8 - ice mod
# s10e original
# op3T lineage
# op7T lineage
# samsung A3 2017
from datetime import datetime
import os.path
import sys
import time
from typing import NoReturn

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb, AdbDevice
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
import pandas as pd
from git.repo.base import Repo

from dearpygui.core import *
from dearpygui.simple import *

# ###############################################################################
#                                Config                                         #
# ###############################################################################

local_folder_path = "./"
adb_key_file = "adb_key"
remote_save_path = "./storage/emulated/0/"
save_file_name = "universal_android_debloater_package_list"
save_file_extension = "csv"
debloater_list_path = "./uad/lists"  # TODO: transform to list,
debloater_list_extension = "sh"
adb_log_file = "log_adb_operations.txt"
package_list_query = "cmd package list packages "
package_list_query_deprecated = "pm list packages "
package_options = [
    ("-s -e", "sys_EN"),
    ("-s -d", "sys_DIS"),
    ("-s -e -u", "sys_EN_pUninst"),
    ("-s -d -u", "sys_DIS_pUninst"),

    ("-3 -e", "3rd_EN"),
    ("-3 -d", "3rd_DIS"),
    ("-3 -e -u", "3rd_EN_pUninst"),
    ("-3 -d -u", "3rd_DIS_pUninst"),
]
# TODO: the logic fns in get_package_list() could be lambdas, defined here

csv_delimiter = ";"  # default: ",", tab is "\t"
csv_encoding = "utf-8-sig"  # unicode
csv_decimal = ","  # the german way is ","

debloat_columns = ["found_info", "is_safe", "source_file", "source_pos", "source_range", "source_descr"]
package_columns = ["package", "type", "enabled", "installed", "via_adb"]
program_name = "Universal Android Debloater UI - v0.4 Alpha"
adb_sleep = 0.5  # s # TODO: test if that makes the experience smoother, sometimes the phone stops to answer

# assemble config
adb_key_file_path = local_folder_path + adb_key_file
remote_package_file_path = remote_save_path + save_file_name + "." + save_file_extension
local_backup_package_file_path = local_folder_path + save_file_name + "_remote_backup." + save_file_extension
local_package_file_path = local_folder_path + save_file_name + "." + save_file_extension
package_option_names = [option[1] for option in package_options]

# ###############################################################################
#                                Git                                            #
# ###############################################################################


def git_update() -> NoReturn:
    global debloater_list_path
    uad_path = "/".join(debloater_list_path.split("/")[0:-1])
    if not os.path.exists(uad_path):
        print(f"-> cloned the git-repo 'universal android debloater'")
        Repo.clone_from("https://gitlab.com/W1nst0n/universal-android-debloater", uad_path)
    else:
        print(f"-> updating uad-scripts")
        repo = Repo(uad_path)
        repo.git.pull()


# ###############################################################################
#                                LogFile                                        #
# ###############################################################################

def save_to_log(action: str, device: str, response: str) -> NoReturn:
    global adb_log_file, local_folder_path
    with open(local_folder_path + adb_log_file, 'a') as file:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        file.write(f"{timestamp} - {device} - '{action}': ")
        file.write(response.replace("\n", " | ").replace("\r", " | ").strip("\t") + "\n")

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

    _device = AdbDeviceUsb()  # TODO: there can be more than one phone, determine with "available", "list" or similar
    _device.connect(rsa_keys=[signer], auth_timeout_s=30)
    # time.sleep(adb_sleep)
    if check_device_availability(_device):
        print(f"-> connected to device per USB")
    return _device


def check_device_availability(_device: AdbDevice) -> bool:
    if _device is None:
        return False
    is_available = _device.available  # TODO: disconnected phone seems still to be available
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
    global package_options, package_list_query
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
    save_to_log(cmd1, device_name, response1)
    save_to_log(cmd2, device_name, response2)
    time.sleep(adb_sleep)
    if with_uninstall:
        response3 = _device.shell(cmd3)
        print(f"-> uninstall package '{package}' with response '{response3}'")
        save_to_log(cmd3, device_name, response3)
        time.sleep(adb_sleep)
    response4 = _device.shell(cmd4)
    print(f"-> clear userdata of package '{package}' with response '{response4}'")
    save_to_log(cmd4, device_name, response4)
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
        save_to_log(cmd1, device_name, response1)
        time.sleep(adb_sleep)
    response2 = _device.shell(cmd2)
    response3 = _device.shell(cmd3)
    print(f"-> enabling package '{package}' with response '{response2}'")
    print(f"-> starting package '{package}' with response '{response3}'")
    save_to_log(cmd2, device_name, response2)
    save_to_log(cmd3, device_name, response3)
    time.sleep(adb_sleep)
    return True


# TODO: backup current phone
# adb backup -apk -all -system -f "${PHONE:-phone}-`date +%Y%m%d-%H%M%S`.adb"

# TODO: store database on device


# ###############################################################################
#                               DEBLOAT SCRIPT                                  #
# ###############################################################################

# import universal android debloater
def parse_debloat_lists(debug: bool = False) -> pd.DataFrame:
    global debloater_list_path, debloater_list_extension, debloat_columns, package_columns
    file_items = [x for x in os.scandir(debloater_list_path) if x.is_file()]  # is List[os.DirEntry]
    package_list = list([])
    for file in file_items:
        item_ext = file.name.split(".")[-1]
        if item_ext.find(debloater_list_extension) < 0:
            continue
        if debug:
            print(f"-> will parse '{file.name}'")
        with open(file, "r", encoding="utf8") as metafile:
            # TODO: encoding had to be specified, because of unusual characters in LG.sh, line 135
            data = metafile.readlines()
            data = [date.replace("\t", "").replace("\r", "").replace("\n", "") for date in data]
            data_len = len(data)
            for data_index in range(data_len):
                # filter for lines with format: text1 "text2" text3 -> text2 is alphanum with .dot, without spaces or /
                fragments = data[data_index].split("\"")
                if (len(fragments) > 3) and debug:
                    print(f"NOTE: filtered out '{fragments}', because of too many >>\"<< in '{file.name}'")
                if len(fragments) != 3:
                    continue
                package_name = fragments[1]
                is_safe = fragments[0].find("#") < 0
                if (package_name.find(".") < 0) or (package_name.find(" ") > 0) or (package_name.find("/") > 0):
                    if debug:
                        print(f"NOTE: filtered out '{package_name}' package -> invalid name-format in '{file.name}'")
                    continue
                # determine start and end of description
                line_min = max(0, data_index - 6)
                for min_index in range(data_index-1, line_min, -1):
                    if len(data[min_index]) < 2:
                        line_min = min_index + 1
                        break
                line_max = min(data_len - 1, data_index + 10)
                for max_index in range(data_index+1, line_max, 1):
                    if len(data[max_index]) < 2:
                        line_max = max_index
                        break
                data_row = [package_name, True, is_safe, file.name, data_index, range(line_min, line_max), data[line_min:line_max]]
                package_list.append(pd.DataFrame([data_row], columns=[package_columns[0]] + debloat_columns))
    print(f"-> parsed debloat lists, got {len(package_list)} entries")
    packages = pd.concat(package_list, ignore_index=True).sort_values(by="package", ascending=True)
    packages.loc[:, "duplicate"] = packages.duplicated(subset=["package"], keep=False)
    packages = packages.reset_index(drop=True)
    return packages


def enrich_package_list(packages: pd.DataFrame, debloats: pd.DataFrame) -> pd.DataFrame:
    global debloat_columns
    packages.loc[:, debloat_columns] = packages["package"].apply(lambda x: lambda_enrich_package(x, debloats))
    return packages


def lambda_enrich_package(package: str, debloat_list: pd.DataFrame) -> pd.Series:
    global debloat_columns
    debloats = debloat_list[debloat_list["package"] == package]
    item = pd.Series(dtype=bool)
    if len(debloats) > 0:
        for column in debloat_columns:
            item[column] = debloats[column].iloc[0]
    else:
        item[debloat_columns[0]] = False
        for column in debloat_columns[1:]:
            item[column] = ""
    return item


# ###############################################################################
#                                dearPyGUI                                      #
# ###############################################################################

def set_default_filter_state() -> NoReturn:
    set_value("text_filter_keywords", "")
    set_value("button_filter_type", 0)
    set_value("button_filter_active", 0)
    set_value("button_filter_safe", 0)


def filter_dataframe(df: pd.DataFrame, column: str, filter_val: int) -> pd.DataFrame:
    if filter_val == 0:
        return df
    elif filter_val == 1:
        return df[df[column] == True]
    elif filter_val == 2:
        return df[df[column] == False]
    else:
        log_error(f"misuse of dataframe-filter!", logger="debuglog")
        return df


def update_table() -> NoReturn:
    global package_data, table_dimension, package_columns, debloat_columns
    type_data = filter_dataframe(package_data, "type", get_value("button_filter_type"))
    type_data.loc[:, "active"] = type_data["enabled"] & type_data["installed"]
    active_data = filter_dataframe(type_data, "active", get_value("button_filter_active"))
    safe_data = filter_dataframe(active_data, "is_safe", get_value("button_filter_safe"))
    keyword_data = safe_data
    keyword_data['source_str'] = keyword_data['source_descr'].apply(lambda x: ', '.join(map(str, x)))
    for keyword in get_value("text_filter_keywords").split(" "):
        match_package = keyword_data["package"].str.contains(keyword)
        match_description = keyword_data["source_str"].str.contains(keyword)
        keyword_data = keyword_data[match_package | match_description]
    keyword_data.loc[:, "type"] = keyword_data["type"].apply(lambda x: "System" if x else "3rd Party")
    data_print = keyword_data[package_columns + debloat_columns[1:-3]]
    set_table_data("table_packages", data_print.values.tolist())
    set_headers("table_packages", data_print.columns.values.tolist())
    log_info(f"updated table, {len(data_print)} items", logger="debuglog")
    table_dimension = data_print.shape
    update_selection_list()
    # TODO: first col should be double as wide, not possible ATM, table-api is getting replaced future dearPyGui release


def update_data() -> NoReturn:
    global device, package_data, debloat_data
    package_data1 = package_data if (len(package_data) > 0) else restore_device_package_list(device)
    package_data1["via_adb"] = False
    package_data2 = read_package_list(device)
    package_data3 = pd.concat([package_data1, package_data2], ignore_index=True)
    package_data4 = package_data3.sort_values(by="via_adb", ascending=False).groupby("package").first().reset_index()
    package_data = enrich_package_list(package_data4, debloat_data)
    log_info(f"read {len(package_data)} packages, {len(package_data[package_data['via_adb'] == False])} only via backup (not adb)", logger="debuglog")


def update_buttons() -> NoReturn:
    global is_connected
    configure_item("button_disconnect", label="Disconnect Device" if is_connected else "Connect Device")
    configure_item("button_update_data", enabled=is_connected)
    configure_item("button_save_data", enabled=is_connected)
    configure_item("text_filter_keywords", enabled=is_connected)
    configure_item("button_filter_type", enabled=is_connected)
    configure_item("button_filter_active", enabled=is_connected)
    configure_item("button_filter_safe", enabled=is_connected)
    configure_item("button_filter_reset", enabled=is_connected)


def filter_update_callback(sender, data) -> NoReturn:
    update_table()


def filter_reset_callback(sender, data) -> NoReturn:
    set_default_filter_state()
    update_table()


def connect_button_callback(sender, data) -> NoReturn:
    global device, user, package_data, debloat_data, is_connected, adb_key_file_path, package_columns, debloat_columns, device_android_sdk
    if is_connected:
        device.close()
        device = None
        package_data = pd.DataFrame(columns=package_columns + debloat_columns)
        log_info(f"Disconnected from device", logger="debuglog")
    else:
        device = connect_device_usb(adb_key_file_path)
        get_device_properties(device)
        log_info(f"connected device='{device_name}', android {device_android_version}", logger="debuglog")
        users = get_device_users(device)
        if len(users) > 1:
            log_info("NOTE: there are several users, will choose first one in list!", logger="debuglog")
            log_info(str(users), logger="debuglog")
        user = users["index"].iloc[0]
        if device_android_sdk < 26:
            log_error("WARNING: Your android version is old (< 8.0).", logger="debuglog")
            log_error("Uninstalled packages can't be restored.", logger="debuglog")
            log_error("The GUI won't stop you from doing so", logger="debuglog")
        update_data()
    update_table()
    is_connected = check_device_availability(device)
    update_buttons()


def update_button_callback(sender, data) -> NoReturn:
    update_data()
    update_table()


def save_button_callback(sender, data) -> NoReturn:
    global debloat_data, package_data, local_package_file_path, csv_delimiter, csv_encoding, csv_decimal
    log_info("will save package-data as csv (local_file_path)", logger="debuglog")
    try:
        # TODO: only for debug for now
        debloat_data.to_csv("./debloat_list.csv", sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    except PermissionError:
        log_error(f"file with debloat_data could not be saved, seems to be open in another program", logger="debuglog")
    try:
        package_data.to_csv(local_package_file_path, sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    except PermissionError:
        log_error(f"file {local_package_file_path} could not be saved, seems to be open in another program", logger="debuglog")


def show_package_info(package: str) -> NoReturn:
    global package_data, debloat_columns
    package_info1 = package_data.loc[package_data["package"] == package, debloat_columns[-1]].iloc[0]
    package_info2 = list([])
    # easiest (most stupid) way to shorten strings, because text-field can't handle line breaks
    # TODO: this should be done earlier on retrieval, we also need a joined version for search (without '#')
    for info in package_info1:
        if len(info) < 60:
            package_info2.append(info)
        elif len(info) < 120:
            package_info2.append(info[0:60])
            package_info2.append(info[60:])
        else:
            package_info2.append(info[0:60])
            package_info2.append(info[60:120])
            package_info2.append(info[120:])
    package_file = package_data.loc[package_data["package"] == package, debloat_columns[-4]].iloc[0]  # TODO: optimize
    package_loc = package_data.loc[package_data["package"] == package, debloat_columns[-3]].iloc[0]
    if len(package_file) > 0:
        package_source = [f"\nSource {package_file}, Line {package_loc}"]
    else:
        package_source = ["package currently not known to debloat-project"]
    package_meta = [package + "\n"] + package_info2 + package_source

    set_value("package_info", "\n".join(package_meta))


def update_selection_list() -> NoReturn:
    global table_selection, table_dimension
    coordinates = get_table_selections("table_packages")
    row_sel_count = table_dimension[0] * [0]
    for coordinate in coordinates:
        row_sel_count[coordinate[0]] += 1
    table_width = table_dimension[1]
    table_selection = list([])
    for row_index in range(len(row_sel_count)):
        col_count = row_sel_count[row_index]
        if col_count == 0:
            continue
        elif col_count == 1:
            for col_index in range(table_width):
                set_table_selection("table_packages", row_index, col_index, True)
            show_package_info(get_table_item("table_packages", row_index, 0))
        elif col_count == table_width - 1:
            for col_index in range(table_width):
                set_table_selection("table_packages", row_index, col_index, False)
            continue
        table_selection.append(get_table_item("table_packages", row_index, 0))

    has_selection = is_connected and (len(table_selection) > 0)
    configure_item("button_sel_clear", enabled=has_selection)
    configure_item("button_sel_enable", enabled=has_selection)
    configure_item("button_sel_disable", enabled=has_selection)
    configure_item("button_sel_install", enabled=has_selection)
    configure_item("button_sel_uninstall", enabled=has_selection)
    # configure_item("button_sel_clear_ud", enabled=has_selection)
    if len(table_selection) > 0:
        log_info(f"{len(table_selection)} packages selected: {table_selection}", logger="debuglog")


def table_callback(sender, data) -> NoReturn:
    update_selection_list()


def packages_enable_callback(sender, data) -> NoReturn:
    global table_selection, device, user, package_data
    for package in table_selection:
        log_info(f"will enable '{package}'", logger="debuglog")
        enable_package(device, package, user, with_install=False)
        package_data.loc[package_data["package"] == package, "enabled"] = True
    backup_device_package_list(device, package_data)
    update_data()
    update_table()
    # TODO: buttons can supply data - the 4 similar FNs can be ONE


def packages_disable_callback(sender, data) -> NoReturn:
    global table_selection, device, user, package_data
    for package in table_selection:
        log_info(f"will disable '{package}'", logger="debuglog")
        disable_package(device, package, user, with_uninstall=False)
        package_data.loc[package_data["package"] == package, "enabled"] = False
    backup_device_package_list(device, package_data)
    update_data()
    update_table()


def packages_install_callback(sender, data) -> NoReturn:
    global table_selection, device, user, package_data
    for package in table_selection:
        log_info(f"will install '{package}'", logger="debuglog")
        enable_package(device, package, user, with_install=True)
        package_data.loc[package_data["package"] == package, "installed"] = True
    backup_device_package_list(device, package_data)
    update_data()
    update_table()


def packages_uninstall_callback(sender, data) -> NoReturn:
    global table_selection, device, user, package_data
    for package in table_selection:
        log_info(f"will uninstall '{package}'", logger="debuglog")
        disable_package(device, package, user, with_uninstall=True)
        package_data.loc[package_data["package"] == package, "installed"] = False
    backup_device_package_list(device, package_data)
    update_data()
    update_table()


# TODO: just a test for now
def packages_clear_userdata_callback(sender, data) -> NoReturn:
    global table_selection, device, user, package_data
    for package in table_selection:
        log_info(f"will clear user-data for '{package}'", logger="debuglog")
        cmd_option = f"--user {user}" if device_android_sdk > 21 else ""
        cmd4 = f"pm clear {cmd_option} {package}"
        response4 = device.shell(cmd4)
        print(f"-> clear userdata of package '{package}' with response '{response4}'")
        save_to_log(cmd4, device_name, response4)
        time.sleep(adb_sleep)
    backup_device_package_list(device, package_data)
    update_data()
    update_table()

def window_resize_callback(sender, data) -> NoReturn:
    global table_height_offset, window_height
    window_size = get_main_window_size()
    if window_size[1] != window_height:
        window_height = window_size[1]
        table_height = window_height - table_height_offset
        configure_item("table_packages", height=table_height)


# ###############################################################################
#                                Program                                        #
# ###############################################################################


if __name__ == '__main__':

    pd.set_option('mode.chained_assignment', None)
    git_update()

    user: int = 0
    device: AdbDevice = None
    device_name: str = None
    device_android_version = 0
    device_android_sdk = 0
    debloat_data: pd.DataFrame = parse_debloat_lists()
    package_data: pd.DataFrame = pd.DataFrame(columns=package_columns + debloat_columns)
    is_connected: bool = False
    table_selection: list = list([])
    table_dimension: Union = (0, 0)
    table_height_offset = 450  # pixels,  window_height - table_height_offset = table_height
    window_height: int = 800

    set_main_window_title(title=program_name)
    set_main_window_size(1000, window_height)
    set_render_callback(callback=window_resize_callback)
    set_theme(theme="Purple")  # fav: Purple, Gold, Light

    with window("main"):
        add_button("button_disconnect",
                   label="Connect",
                   tip="Connect or Disconnects to Device",
                   width=150,
                   callback=connect_button_callback)

        add_same_line(spacing=20)
        add_button("button_update_data",
                   label="Update Package-Data",
                   tip="fetches package-information from device",
                   enabled=is_connected,
                   width=150,
                   callback=update_button_callback)

        add_same_line(spacing=20)
        add_button("button_save_data",
                   label="Save Data locally",
                   tip="Stores a CSV locally in the program-directory",
                   enabled=is_connected,
                   width=150,
                   callback=save_button_callback)

        add_spacing(count=5, name="spacing1")
        add_text("Package-Filter:")

        add_same_line(spacing=10)
        add_input_text(name="text_filter_keywords",
                       hint="",
                       label="",
                       width=200,
                       tip="enter custom keywords to filter list (package name and description)",
                       enabled=is_connected,
                       callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_type",
                         items=["show all", "only system", "only 3rd party"],
                         tip="Filter for package type - system or 3rd Party",
                         enabled=is_connected,
                         callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_active",
                         items=["show all", "only active", "only inactive"],
                         tip="Filter for active Packages (enabled and installed)",
                         enabled=is_connected,
                         callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_safe",
                         items=["show all", "only safe", "only unsafe"],
                         tip="Filter for known non-bricking Packages (can still ruin your user experience)",
                         enabled=is_connected,
                         callback=filter_update_callback)

        add_same_line(spacing=30)
        add_button("button_filter_reset",
                   label="Reset",
                   tip="filters are set to default",
                   enabled=is_connected,
                   callback=filter_reset_callback)

        add_spacing(count=2, name="spacing2")
        add_table("table_packages",
                  ["not", "updated", "yet"],
                  height=window_height - table_height_offset,
                  callback=table_callback)
        # TODO: maybe switch with listbox, could expand easier, but allows only one selection
        # TODO: another good way would be to get hover-element of table and show a tooltip, but this is not possible right now

        add_spacing(count=2, name="spacing3")
        add_text("Package Actions:")

        add_same_line(spacing=10)
        add_button("button_sel_clear",
                   label="Clear Selection",
                   tip="",
                   enabled=is_connected,
                   callback=filter_update_callback)

        add_same_line(spacing=20)
        add_button("button_sel_enable",
                   label="Enable Selected",
                   tip="",
                   enabled=is_connected,
                   callback=packages_enable_callback)

        add_same_line(spacing=20)
        add_button("button_sel_disable",
                   label="Disable Selected",
                   tip="",
                   enabled=is_connected,
                   callback=packages_disable_callback)

        add_same_line(spacing=20)
        add_button("button_sel_install",
                   label="Install Selected",
                   tip="Re-Install if possible",
                   enabled=is_connected,
                   callback=packages_install_callback)

        add_same_line(spacing=20)
        add_button("button_sel_uninstall",
                   label="UnInstall Selected",
                   tip="",
                   enabled=is_connected,
                   callback=packages_uninstall_callback)

        '''
        add_same_line(spacing=20)
        add_button("button_sel_clear_ud",
                   label="Clear Userdata Selected (DO NOT USE - JUST A TEST)",
                   tip="",
                   enabled=is_connected,
                   callback=packages_clear_userdata_callback)
        '''

        add_spacing(count=7, name="spacing3")
        add_input_text("package_info",
                    width=500,
                    label="",
                    height=230,
                       readonly=True,multiline=True)

        add_same_line(spacing=10)
        add_logger("debuglog",
                   log_level=1,
                   width=450,
                   height=230,
                   auto_scroll=True, auto_scroll_button=False,
                   copy_button=False, clear_button=False,
                   filter=False)
        configure_item("debuglog", auto_scroll=True)  # TODO: file bugreport, auto_scroll=True in initializer does not work

    # TODO: just define objects in main, config later in start-routine, can replace/extend the update-gui callback
    # TODO: bring logger to second tab, brings cleaner interface
    # TODO: add a notification, that info is about to be improved
    start_dearpygui(primary_window="main")
    stop_dearpygui()

# TODO: initial unfinished (and now most likely incompatible) cmd line version
'''
if __name__ == '__main__':
    device = connect_device_usb(adb_key_file_path)
    users = get_device_users(device)
    if len(users) > 1:
        print("NOTE: there are several users, will choose first one in list!")
        print(users)
    user = users["index"].iloc[0]

    #pull_device_package_list_backup(device)
    #push_device_package_list_backup(device, "./requirements.txt")
    #pull_device_package_list_backup(device)

    #print(get_device_properties(device))
    #disable_package(device, "com.android.stk", user)

    debloat_data = parse_debloat_lists()
    try:
        # TODO: only for debug for now
        debloat_data.to_csv("./debloat_list.csv", sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    except PermissionError:
        print(f"ERROR: file with debloat_data could not be saved, seems to be open in another program")
    package_data = read_package_list(device)
    package_data = enrich_package_list(package_data, debloat_data)

    start_dearpygui()
    # TODO: add UI here

    try:
        package_data.to_csv(local_file_path, sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    except PermissionError:
        print(f"ERROR: file {local_file_path} could not be saved, seems to be open in another program")
    device.close()  # TODO: transform into fn or class-method
'''
