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
        log_info(f"-> cloned the git-repo 'universal android debloater'", logger="debuglog")
        Repo.clone_from("https://gitlab.com/W1nst0n/universal-android-debloater", uad_path)
    else:
        log_info(f"updating local git-repo of debloat-scripts", logger="debuglog")
        repo = Repo(uad_path)
        repo.git.pull()


# ###############################################################################
#                                LogFile                                        #
# ###############################################################################


def save_to_log(_device: str, package: str, action: str, response: str) -> NoReturn:
    with open(cfg.adb_log_file_path, 'a') as file:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        file.write(f"{timestamp} - {_device} - {package} - '{action}': ")
        file.write(response.replace("\n", ";").replace("\r", ";").strip("\t") + "\n")

# ###############################################################################
#                                Pandas                                         #
# ###############################################################################


def save_dataframe(df: pd.DataFrame, path: str) -> bool:
    # TODO: refactor to proper fn with try catch, used at least 3x
    try:
        df.to_csv(path,
                  sep=cfg.csv_delimiter,
                  encoding=cfg.csv_encoding,
                  decimal=cfg.csv_decimal)
    except PermissionError:
        log_error(f"file {path} could not be saved -> open in another program?",
                  logger="debuglog")
    return True


def load_dataframe(path: str) -> pd.DataFrame:
    return pd.read_csv(path,
                       sep=cfg.csv_delimiter,
                       encoding=cfg.csv_encoding,
                       decimal=cfg.csv_decimal)
