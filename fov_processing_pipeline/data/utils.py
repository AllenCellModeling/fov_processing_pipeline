import warnings
from sys import platform

import pandas as pd
import numpy as np

from ..utils import int2rand

REQUIRED_COLUMNS = [
    "ProteinDisplayName",
    "CellLine",
    "FOVId"
]


def clean_columns(cell_data):
    ############################################
    # Adjust file paths
    ############################################

    if platform == "linux" or platform == "linux2":
        # linux
        pass
    elif platform == "darwin":
        # if we're in osx, we change all the read paths from
        # /allen/programs/allencell/data/...
        # to
        # ./data/...

        for column in cell_data.columns:
            if "ReadPath" in column:
                cell_data[column] = [
                    readpath.replace("/allen/programs/allencell/", "./")
                    for readpath in cell_data[column]
                ]
    else:
        raise NotImplementedError(
            "OSes other than Linux and Mac are currently not supported."
        )

    ############################################
    # Remove unnecessary columns
    ############################################

    drop_columns = [column for column in cell_data.columns if "FileId" in column] + [
        "StructEducationName",
        "StructureSegmentationAlgorithmVersion",
        "RunId",
    ]

    cell_data = cell_data.drop(drop_columns, axis=1)

    ############################################
    # Assign random numbers to IDs
    ############################################

    id_columns = [column for column in cell_data.columns if column[-2:] == "Id"]

    for id_column in id_columns:
        cell_data["{}_rng".format(id_column)] = [
            int2rand(int(my_id)) for my_id in cell_data[id_column]
        ]

    return cell_data


def cell_data_to_fov_data(cell_data):
    _, FOVId_index = np.unique(cell_data["FOVId"], return_index=True)

    fov_data = cell_data.iloc[FOVId_index]

    # Drop any columns that are per-cell information
    drop_columns = [
        column
        for column in fov_data.columns
        if ("cell" in column.lower() and column.lower() != "cellline")
        | ("mito" in column.lower())
    ]

    fov_data = fov_data.drop(drop_columns, axis=1)

    return fov_data

def trim_data_by_cellline_fov_count(df, n_fovs):

    ############################################
    # For all cell lines, trim number of FOVS to n_fovs (or less)
    ############################################

    keep_fov_ids = []
    for id in pd.unique(df["CellLine"]):
        df_struct = df[df["CellLine"] == id]

        # make sure the desired number of fovs isn't greater than the number of available fovs
        if n_fovs <= pd.unique(df_struct["FOVId"]).shape[0]:
            keep_fov_ids.extend(
                list(np.sort(pd.unique(df_struct["FOVId_rng"]))[:n_fovs],)
            )

        else:
            warnings.warn(
                "Desired number FOVs is greater than original number FOVS for "
                + id
                + "."
            )
            warnings.warn("Keeping all FOVs for this cell line.")
            keep_fov_ids.extend(pd.unique(df_struct["FOVId_rng"]))

    return df[df["FOVId_rng"].isin(keep_fov_ids)]


def trim_data(df, protein_list=None, n_fovs=100):

    ############################################
    # Trim dataset to contain only the given cell lines, with only the set number of FOVs or less
    # preset cell line IDs are: ER, Fibrillarin (Nucleolus), Golgi, Nucleophosmin (Nucleolus), Alpha Actinin
    # listing of cell lines by ID can be found at: https://www.allencell.org/cell-catalog.html
    ############################################

    if protein_list is None:
        protein_list = [
            "Sec61 beta",  # er
            "Fibrillarin",  # nucleolus, DFC
            "Nucleophosmin",  # nucleolus, GC
            "Sialyltransferase 1",  # golgi,
            "Alpha-actinin-1",  # alpha actinin
            "Non-muscle myosin heavy chain IIB",  # actomyosin bundles
            "Lamin B1",  # nuclear lamin
            "Alpha-tubulin",
        ]

    cell_line_trim = df[df["ProteinDisplayName"].isin(protein_list)]

    # cell_line_trim = trim_data_by_cellline(df, cell_line_ids)
    if n_fovs is not None and n_fovs != -1:
        fov_trim = trim_data_by_cellline_fov_count(cell_line_trim, n_fovs)

    return fov_trim

def clean_cell_data(cell_data: pd.DataFrame, protein_list=None, n_fovs=100):
    cell_data = clean_columns(cell_data)

    cell_data = trim_data(cell_data, protein_list=protein_list, n_fovs=n_fovs)

    fov_data = cell_data_to_fov_data(cell_data)

    return cell_data, fov_data
