import pandas as pd
from adb_shell.adb_device import AdbDevice

# ###############################################################################
#                                Program Config                                 #
# ###############################################################################

adb_key_file_path = "./adb_key"
remote_save_path = "./storage/emulated/0/"
save_file_name = "universal_android_debloater_package_list"
save_file_extension = "csv"
debloater_list_path = "./uad/lists"  # TODO: transform to list,
debloater_list_extension = "sh"
adb_log_file_path = "./log_adb_operations.txt"


# TODO: the logic fns in get_package_list() could be lambdas, defined here
program_name = "Universal Android Debloater UI - v0.45 Alpha"

# assemble config
remote_package_file_path = remote_save_path + save_file_name + "." + save_file_extension
local_backup_package_file_path = "./" + save_file_name + "_remote_backup." + save_file_extension
local_package_file_path = "./" + save_file_name + "." + save_file_extension

# ###############################################################################
#                                ADB Config                                     #
# ###############################################################################

adb_sleep = 0.5  # s # TODO: test if that makes the experience smoother, sometimes the phone stops to answer

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

csv_delimiter = ";"  # default: ",", tab is "\t"
csv_encoding = "utf-8-sig"  # unicode
csv_decimal = ","  # the german way is ","

debloat_columns = ["found_info", "is_safe", "source_file", "source_pos", "source_range", "source_descr"]
package_columns = ["package", "type", "enabled", "installed", "via_adb"]
package_option_names = [option[1] for option in package_options]

# ###############################################################################
#                                Program Globals                                #
# ###############################################################################

pd.set_option('mode.chained_assignment', None)

user: int = 0
device: AdbDevice = None
device_name: str = None
device_android_version = 0
device_android_sdk = 0
debloat_data: pd.DataFrame = pd.DataFrame(columns=package_columns[:0] + debloat_columns)
package_data: pd.DataFrame = pd.DataFrame(columns=package_columns + debloat_columns)
is_connected: bool = False
