## Universal Android Debloater UI

- runs on python and dearpygui
- linux, windows and macOS should be supported
  - but only windows is tested right now
- should support all android versions
  - but only android 10 is tested right now
- NOTE: this is a prototype

### Installation

- clone this repository
- (optional) clone [UAD](https://gitlab.com/W1nst0n/universal-android-debloater) repo to sub-folder "uad", so that the lists are in "./uad/lists/"
- make sure python 3.6+ is on your system
- run:
  
        pip install -r requirements.txt

### Usage

- run main.py -> UI should appear
- (optional) copy your adb-key to this folder, otherwise a new one is generated and your phone wants confirmation on first connect
- connect your device
- data is automatically saved and fetched on device on local data-partition as "universal_android_debloater_package_list.csv"
  - this ensures that you see uninstalled packages even if adb does not show them anymore
- you can filter for keywords above the table or for values on specific columns by clicking the cell in the first row
- make your selection on packages and choose an action below the table
  - note1: you should only remove packages that are safe
  - note2: even some safe packages can ruin your experience if you got no replacement
  - note3: information about the packages should be shown as you click on the corresponding row

### Todo

- add screenshot
- auto save meta-data on device
- (tested) support for older android versions
- better meta-data support for known packages
- generate binaries, mostly windows because linux and mac already ship with python

