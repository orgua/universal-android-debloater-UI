# Devices to Test:
# s8 - alexis, https://forum.xda-developers.com/t/alexis-rom-9-1_dtj1_10-2020-patches-27-10-2020-ported-s10-stuffs-s9wallpapers.3753975/
# s8 - ice mod
# s10e original
# op3T lineage
# op7T lineage
# samsung A3 2017

from dearpygui.core import *
from dearpygui.simple import *

import configuration as cfg
from framework_dearpygui import *
from framework_misc import git_update

# ###############################################################################
#                                Program                                        #
# ###############################################################################


if __name__ == '__main__':

    set_main_window_title(title=cfg.program_name)
    set_main_window_size(1000, window_height)
    set_render_callback(callback=window_resize_callback)
    set_theme(theme="Purple")  # fav: Purple, Gold, Light
    set_start_callback(callback=program_start_callback)

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
                   enabled=False,
                   width=150,
                   callback=update_button_callback)

        add_same_line(spacing=20)
        add_button("button_save_data",
                   label="Save Data locally",
                   tip="Stores a CSV locally in the program-directory",
                   enabled=False,
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
                       enabled=False,
                       callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_type",
                         items=["show all", "only system", "only 3rd party"],
                         tip="Filter for package type - system or 3rd Party",
                         enabled=False,
                         callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_active",
                         items=["show all", "only active", "only inactive"],
                         tip="Filter for active Packages (enabled and installed)",
                         enabled=False,
                         callback=filter_update_callback)

        add_same_line(spacing=10)
        add_radio_button("button_filter_safe",
                         items=["show all", "only safe", "only unsafe"],
                         tip="Filter for known non-bricking Packages (can still ruin your user experience)",
                         enabled=False,
                         callback=filter_update_callback)

        add_same_line(spacing=30)
        add_button("button_filter_reset",
                   label="Reset",
                   tip="filters are set to default",
                   enabled=False,
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
                   enabled=False,
                   callback=filter_update_callback)

        add_same_line(spacing=20)
        add_button("button_sel_enable",
                   label="Enable Selected",
                   tip="",
                   enabled=False,
                   callback=packages_enable_callback)

        add_same_line(spacing=20)
        add_button("button_sel_disable",
                   label="Disable Selected",
                   tip="",
                   enabled=False,
                   callback=packages_disable_callback)

        add_same_line(spacing=20)
        add_button("button_sel_install",
                   label="Install Selected",
                   tip="Re-Install if possible",
                   enabled=False,
                   callback=packages_install_callback)

        add_same_line(spacing=20)
        add_button("button_sel_uninstall",
                   label="UnInstall Selected",
                   tip="",
                   enabled=False,
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
                       width=500, height=230,
                       label="",
                       readonly=True,multiline=True)

        add_same_line(spacing=10)
        add_logger("debuglog",
                   log_level=1, filter=False,
                   width=450, height=230,
                   auto_scroll=True, auto_scroll_button=False,
                   copy_button=False, clear_button=False)

    # TODO: just define objects in main, config later in start-routine, can replace/extend the update-gui callback
    # TODO: bring logger to second tab, brings cleaner interface
    # TODO: add a notification, that info is about to be improved
    start_dearpygui(primary_window="main")
    stop_dearpygui()
