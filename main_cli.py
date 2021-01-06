from framework_adb import *
from framework_debloat import *
from configuration import *

# TODO: initial, unfinished (and now most likely incompatible) cmd line interface
# TODO: try https://github.com/tiangolo/typer to put together a proper CLI

# ###############################################################################
#                                Program                                        #
# ###############################################################################


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

    try:
        package_data.to_csv(local_file_path, sep=csv_delimiter, encoding=csv_encoding, decimal=csv_decimal)
    except PermissionError:
        print(f"ERROR: file {local_file_path} could not be saved, seems to be open in another program")
    device.close()  # TODO: transform into fn or class-method
