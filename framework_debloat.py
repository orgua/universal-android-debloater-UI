import os.path
from typing import NoReturn

import pandas as pd
from dearpygui.core import log_error, log_info

import configuration as cfg

# ###############################################################################
#                               DEBLOAT Globals                                 #
# ###############################################################################

debloat_data: pd.DataFrame = pd.DataFrame(columns=cfg.package_columns[:0] + cfg.debloat_columns)

# ###############################################################################
#                               DEBLOAT SCRIPT                                  #
# ###############################################################################


def parse_debloat_lists(debug: bool = False) -> NoReturn:
    global debloat_data
    file_items = [x for x in os.scandir(cfg.debloater_list_path) if x.is_file()]  # is List[os.DirEntry]
    package_list = list([])
    for file in file_items:
        item_ext = file.name.split(".")[-1]
        if item_ext.find(cfg.debloater_list_extension) < 0:
            continue
        if debug:
            print(f"-> will parse '{file.name}'")
        with open(file, "r", encoding="utf8") as metafile:
            # TODO: encoding had to be specified, because of unusual characters in LG.sh, line 135
            data = metafile.readlines()
            data = [date.replace("\t", "").replace("\r", "").replace("\n", "") for date in data]
            data_len = len(data)
            for data_index in range(data_len):
                # filter for lines with format: text1 "text2" text3 -> text2 is alphanum with .dot, without spaces or /
                fragments = data[data_index].split("\"")
                if (len(fragments) > 3) and debug:
                    print(f"NOTE: filtered out '{fragments}', because of too many >>\"<< in '{file.name}'")
                if len(fragments) != 3:
                    continue
                package_name = fragments[1]
                is_safe = fragments[0].find("#") < 0
                if (package_name.find(".") < 0) or (package_name.find(" ") > 0) or (package_name.find("/") > 0):
                    if debug:
                        print(f"NOTE: filtered out '{package_name}' package -> invalid name-format in '{file.name}'")
                    continue
                # determine start and end of description
                line_min = max(0, data_index - 6)
                for min_index in range(data_index-1, line_min, -1):
                    if len(data[min_index]) < 2:
                        line_min = min_index + 1
                        break
                line_max = min(data_len - 1, data_index + 10)
                for max_index in range(data_index+1, line_max, 1):
                    if len(data[max_index]) < 2:
                        line_max = max_index
                        break
                data_row = [package_name, True, is_safe, file.name, data_index, range(line_min, line_max), data[line_min:line_max]]
                package_list.append(pd.DataFrame([data_row], columns=[cfg.package_columns[0]] + cfg.debloat_columns))
    log_info(f"[UAD] parsed debloat lists ({len(package_list)} entries)", logger="debuglog")
    packages = pd.concat(package_list, ignore_index=True).sort_values(by="package", ascending=True)
    packages.loc[:, "duplicate"] = packages.duplicated(subset=["package"], keep=False)
    packages = packages.reset_index(drop=True)
    debloat_data = packages


def enrich_package_list(packages: pd.DataFrame) -> pd.DataFrame:
    packages.loc[:, cfg.debloat_columns] = packages["package"].apply(lambda x: lambda_enrich_package(x))
    return packages


def lambda_enrich_package(package: str) -> pd.Series:
    global debloat_data
    debloats = debloat_data[debloat_data["package"] == package]
    item = pd.Series(dtype=bool)
    if len(debloats) > 0:
        for column in cfg.debloat_columns:
            item[column] = debloats[column].iloc[0]
    else:
        item[cfg.debloat_columns[0]] = False
        for column in cfg.debloat_columns[1:]:
            item[column] = ""
    return item
