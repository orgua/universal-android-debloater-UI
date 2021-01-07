import framework_adb as adb_fw
import configuration as cfg
import framework_debloat as uad_fw
import framework_misc as misc

# TODO: initial, unfinished (and now most likely incompatible) cmd line interface
# TODO: try https://github.com/tiangolo/typer to put together a proper CLI

# ###############################################################################
#                                Program                                        #
# ###############################################################################

# This code just pulls package overview from device and saves it as csv
if __name__ == '__main__':
    adb_fw.connect_device_usb()
    adb_fw.update_device_properties()
    uad_fw.parse_debloat_lists()
    adb_fw.update_package_data()
    misc.save_dataframe(adb_fw.device_packages, cfg.local_package_file_path)
    adb_fw.disconnect_device()
