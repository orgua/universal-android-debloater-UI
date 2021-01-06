from datetime import datetime
import os.path
from typing import NoReturn
from git.repo.base import Repo

from configuration import debloater_list_path, adb_log_file_path

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


def save_to_log(_device: str, package: str, action: str, response: str) -> NoReturn:
    global adb_log_file_path
    with open(adb_log_file_path, 'a') as file:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        file.write(f"{timestamp} - {_device} - {package} - '{action}': ")
        file.write(response.replace("\n", ";").replace("\r", ";").strip("\t") + "\n")
