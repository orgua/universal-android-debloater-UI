from setuptools import setup

setup(
    name='Universal Android Debloater UI',
    version='0.4',
    packages=['UAD-UI'],
    install_requires=['adb-shell[async, usb]', 'pandas', 'dearpygui', 'gitpython', 'setuptools'],
    url='https://github.com/orgua/universal-android-debloater-UI',
    license='GPL3',
    author='ingmo',
    author_email='name@game.com',
    description='tdb',
    entry_points={"GUI": ["uad=__main__:main"]},
)

# TODO: pip install -r requirements.txt
# TODO: add pyInstaller to create executable
# https://realpython.com/pyinstaller-python/


# features
# - work with current packages on device
# - shows status of packages: sys or 3rd party, enables | disabled, installed | uninstalled
# - crossreference packages to debloat-scripts - if found it shows: safe_to_remove, source_file
# - UI
#    - sort and filter table
#    - connect and reconnect to device
#    - log-window

# planned
# - TCP-connection to device
# - group and meta-data for the packages
# - load and store debloat-config on device
# -
# -
# -
