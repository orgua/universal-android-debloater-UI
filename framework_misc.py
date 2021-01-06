from datetime import datetime
import os.path
from typing import NoReturn
from git.repo.base import Repo

import pandas as pd
from dearpygui.core import log_error, log_info

import configuration as cfg

# ###############################################################################
#                                Git                                            #
# ###############################################################################


def git_update() -> NoReturn:
    uad_path = "/".join(cfg.debloater_list_path.split("/")[0:-1])
    if not os.path.exists(uad_path):
        Repo.clone_from("https://gitlab.com/W1nst0n/universal-android-debloater", uad_path)
        log_info(f"[GIT] cloned the repo 'universal android debloater'", logger="debuglog")
    else:
        repo = Repo(uad_path)
        repo.git.pull()
        log_info(f"[GIT] updated local repo of debloat-scripts", logger="debuglog")


# ###############################################################################
#                                LogFile                                        #
# ###############################################################################


def save_to_log(_device: str, package: str, action: str, response: str) -> NoReturn:
    try:
        with open(cfg.adb_log_file_path, 'a') as file:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            file.write(f"{timestamp} - {_device} - {package} - '{action}': ")
            file.write(response.replace("\n", ";").replace("\r", ";").strip("\t") + "\n")
    except PermissionError:
        log_error(f"[LOG] '{cfg.adb_log_file_path}' could not be modified -> open in another program?", logger="debuglog")

# ###############################################################################
#                                Pandas CSV                                     #
# ###############################################################################


def save_dataframe(df: pd.DataFrame, path: str) -> bool:
    # TODO: refactor to proper fn with try catch, used at least 3x
    try:
        df.to_csv(path,
                  sep=cfg.csv_delimiter,
                  encoding=cfg.csv_encoding,
                  decimal=cfg.csv_decimal)
    except PermissionError:
        log_error(f"[CSV] '{path}' could not be saved -> open in another program?", logger="debuglog")
    return True


def load_dataframe(path: str) -> pd.DataFrame:
    try:
        data = pd.read_csv(path,
                           sep=cfg.csv_delimiter,
                           encoding=cfg.csv_encoding,
                           decimal=cfg.csv_decimal)
    except FileNotFoundError:
        log_error(f"[CSV] '{path}' could not be opened -> does it excist?", logger="debuglog")
        data = pd.DataFrame()
    return data
