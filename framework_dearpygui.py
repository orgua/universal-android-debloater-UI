from typing import NoReturn
import time

from dearpygui.core import *
from dearpygui.simple import *
import pandas as pd

import framework_adb  as adb_fw
import framework_debloat as uad_fw
import framework_misc as misc
import configuration as cfg

# ###############################################################################
#                                GUI Globals                                    #
# ###############################################################################

table_height_offset = 450  # pixels,  window_height - table_height_offset = table_height
window_height: int = 800

table_selection: list = list([])
table_dimension: Union = (0, 0)

# ###############################################################################
#                                dearPyGUI                                      #
# ###############################################################################
# TODO: move functionality from these FNs to the other frameworks (mostly adb)


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
    global table_dimension
    type_data = filter_dataframe(adb_fw.device_packages, "type", get_value("button_filter_type"))
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
    data_print = keyword_data[cfg.package_columns + cfg.debloat_columns[1:-3]]
    set_table_data("table_packages", data_print.values.tolist())
    set_headers("table_packages", data_print.columns.values.tolist())
    log_info(f"updated table, {len(data_print)} items", logger="debuglog")
    table_dimension = data_print.shape
    update_selection_list()
    # TODO: first col should be double as wide, not possible ATM, table-api is getting replaced future dearPyGui release


def update_buttons() -> NoReturn:
    # TODO: add items from update_selection_list
    # TODO: rename update_gui_items_state_enabled
    dev_state = adb_fw.device_is_connected
    configure_item("button_disconnect", label="Disconnect Device" if dev_state else "Connect Device")
    configure_item("button_update_data", enabled=dev_state)
    configure_item("button_save_data", enabled=dev_state)
    configure_item("text_filter_keywords", enabled=dev_state)
    configure_item("button_filter_type", enabled=dev_state)
    configure_item("button_filter_active", enabled=dev_state)
    configure_item("button_filter_safe", enabled=dev_state)
    configure_item("button_filter_reset", enabled=dev_state)


def filter_update_callback(sender, data) -> NoReturn:
    update_table()


def filter_reset_callback(sender, data) -> NoReturn:
    set_default_filter_state()
    update_table()


def connect_button_callback(sender, data) -> NoReturn:
    if adb_fw.device_is_connected:
        adb_fw.disconnect_device()
    else:
        adb_fw.connect_device_usb()
        if adb_fw.device is None:
            log_error(f"not able to connect to any device", logger="debuglog")
            return
        adb_fw.update_package_data()
    update_table()
    update_buttons()


def update_button_callback(sender, data) -> NoReturn:
    adb_fw.update_package_data()
    update_table()


def save_button_callback(sender, data) -> NoReturn:
    global csv_delimiter, csv_encoding, csv_decimal
    log_info("will save package-data as csv (local_file_path)", logger="debuglog")
    misc.save_dataframe(uad_fw.debloat_data, "./debloat_list.csv") # TODO: only for debug for now
    misc.save_dataframe(adb_fw.device_packages, cfg.local_package_file_path)


def show_package_info(package: str) -> NoReturn:
    package_data = adb_fw.device_packages
    package_info1 = package_data.loc[package_data["package"] == package, cfg.debloat_columns[-1]].iloc[0]
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
    package_file = package_data.loc[package_data["package"] == package, cfg.debloat_columns[-4]].iloc[0]  # TODO: optimize
    package_loc = package_data.loc[package_data["package"] == package, cfg.debloat_columns[-3]].iloc[0]
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

    has_selection = adb_fw.device_is_connected and (len(table_selection) > 0)
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
    global table_selection
    for package in table_selection:
        adb_fw.enable_package(package, with_install=False)
        log_info(f"enabled '{package}'", logger="debuglog")
    adb_fw.backup_device_package_list()
    adb_fw.update_package_data()
    update_table()
    # TODO: buttons can supply data - the 4 similar FNs can be ONE


def packages_disable_callback(sender, data) -> NoReturn:
    global table_selection
    for package in table_selection:
        adb_fw.disable_package(package, with_uninstall=False)
        log_info(f"disabled '{package}'", logger="debuglog")
    adb_fw.backup_device_package_list()
    adb_fw.update_package_data()
    update_table()


def packages_install_callback(sender, data) -> NoReturn:
    global table_selection
    for package in table_selection:
        adb_fw.enable_package(package, with_install=True)
        log_info(f"installed '{package}'", logger="debuglog")
    adb_fw.backup_device_package_list()
    adb_fw.update_package_data()
    update_table()


def packages_uninstall_callback(sender, data) -> NoReturn:
    global table_selection
    for package in table_selection:
        adb_fw.disable_package(package, with_uninstall=True)
        log_info(f"uninstalled '{package}'", logger="debuglog")
    adb_fw.backup_device_package_list()
    adb_fw.update_package_data()
    update_table()


# TODO: just a test for now
def packages_clear_userdata_callback(sender, data) -> NoReturn:
    global table_selection
    for package in table_selection:
        adb_fw.clear_userdata_of_package(package)
        log_info(f"cleared user-data for '{package}'", logger="debuglog")
    adb_fw.backup_device_package_list()
    adb_fw.update_package_data()
    update_table()


def window_resize_callback(sender, data) -> NoReturn:
    global table_height_offset, window_height
    window_size = get_main_window_size()
    if window_size[1] != window_height:
        window_height = window_size[1]
        table_height = window_height - table_height_offset
        configure_item("table_packages", height=table_height)


def program_start_callback(sender, data) -> NoReturn:
    misc.git_update()
    uad_fw.parse_debloat_lists()
