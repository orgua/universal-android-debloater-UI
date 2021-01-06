## Universal Android Debloater UI

This Repository offers a GUI for the awesome [UAD-Project](https://gitlab.com/W1nst0n/universal-android-debloater)

**NOTE: this is a prototype for now**

### Features:

- Linux, Windows and MacOS should be supported (Windows and Linux is tested and works)
  - runs on Python and dearpygui
- should support all versions of Android
  - but only android 10 is tested right now
- checks packages on device against packages known to debloater-tool
	- a fresh samsung S10e has ~120 packages that can be disabled without loosing comfort
    - minimizes wakeups that drain battery, ram-usage, security concerns because of questionable manufacturer / carrier apps
- filter for package-type, keywords, enable-status and remove-recommendation
- packages can be enabled, disabled, installed and uninstalled
- manually save current package data as csv locally
- auto-save meta-data on device (info stays even if adb does not show it anymore)
- resizing windows adapts the table
- log of adb operations - timestamp, device, shell-operation and response


### Installation & Requirements

- you need a 64bit System due to the dearpygui-framework
- make sure python 3.6+ is on your system
- installation and execution need a terminal for now
- probably not every step is necessary on your system
- (optional) copy your adb-key to this folder, otherwise a new one is generated and your phone wants a confirmation on first connect
- (optional) to not mess with you python-setup, you can setup a [virtual-env](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/26/python-virtual-env/) 
- (optional) if you cloned this repo you can just update by executing `git pull` inside the project folder

**Linux** (tested with Mint):

```console
sudo apt install python3-pip  
sudo apt install git

git clone https://github.com/orgua/universal-android-debloater-UI.git
cd universal-android-debloater-UI

pip install -r requirements.txt

py main_gui.py
```

**Windows 10**:

- download and install the newest python with pip
- download and decompress these project sources into a folder
- open cmd-terminal (with admin-rights if you don't plan to use virtual-env and your python install is system-wide)
- run:

```console
pip install --upgrade pip
pip install -r requirements.txt

py main_gui.py
```

**MacOS** (with python and git installed):

```console
sudo easy_install pip
sudo pip install --upgrade pip

git clone https://github.com/orgua/universal-android-debloater-UI.git
cd universal-android-debloater-UI

pip install -r requirements.txt

py main_gui.py
 ```

### Usage

- WARNING AS ALWAYS: always make a full nandroid / twrp backup before changing the system!
- config your phone to allow adb shell (see debloater project for details)
- run `py main_gui.py` -> UI should appear
- connect your device
- data is automatically saved and fetched on device on local data-partition as "universal_android_debloater_package_list.csv"
  - this ensures that you see uninstalled packages even if adb does not show them anymore
- you can filter for keywords above the table or for values on specific columns by clicking the cell in the first row
- make your selection on packages and choose an action below the table, but consider the following warning notes
  - **you should only remove packages that are marked safe**
  - **even some safe packages can ruin your experience if you got no replacement (launcher, keyboard, ..)**
  - **watch out for packages that are considered safe but have another device-brand or "pending.sh" as source**
  - information about the packages should be shown as you click on the corresponding row
- try rebooting and test basic functionality
- phone shows demanding apps in the battery-usage options and ram-horders can be found in the memory-options (hidden dev menu)
- (optional) deactivate adb after you are finished
  
![screenshot](./media/screenshot_alpha.png)

### Todo

- find a way to make first column wider, not possible atm
- (tested) support for older android versions
- connect via TCP
- cleanup GUI, bring adb-output and debug to separate tabs
- add some examples from different manufacturers
- better meta-data support for known packages
- generate binaries, mostly windows because linux and mac already ship with python
  - https://pypi.org/project/crossroad/
- meta-data that would be helpful for known packages (use, where it applies)
  - package_name: name that ADB sees
  - program_name: name in UI, can be language dependant, but should default to english
  - keywords: descriptive words that allow grouping, like "samsung, bixby"
  - dependence_for: allows to warn user if this would break something
  - depending_on: (see comment right above)
  - safe_to_remove: bool
  - description: text like in current lists
  - replacement_recommended: some thing open source and light on resources, similar fn
- better packet info could be stored on a per-file basis or like now in brand specific files, but maybe switch to yaml or similar
- cleanup source, commiting to gui would save 1/5 LOC, but make future cli harder 
