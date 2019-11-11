import lkaccess
import lkaccess.contexts
import pandas as pd
import numpy as np
import warnings
from sys import platform


from .utils import int2rand


def get_cell_data():

    # returns a datframe where every row is a cell

    use_staging = False

    ############################################
    # Get the basic cell-level data from Labkey
    ############################################

    # Create labkey connection
    if use_staging:
        # I dont know what this is
        lk = lkaccess.LabKey(server_context=lkaccess.contexts.STAGE)
    else:
        lk = lkaccess.LabKey(server_context=lkaccess.contexts.PROD)

    # Get pipeline 4 data
    data = pd.DataFrame(lk.dataset.get_pipeline_4_production_data())

    # Get cell line data from some other location in labkey
    cell_line_data = lk.select_rows_as_list(
        schema_name="celllines",
        query_name="CellLineDefinition",
        columns=["CellLineId", "CellLineId/Name", "StructureId/Name", "ProteinId/Name"],
    )
    cell_line_data = pd.DataFrame(cell_line_data)

    # Merge the pipeline 4 and cell line data
    data = data.merge(cell_line_data, how="left", on="CellLineId")

    # Finish preparing the jobs table
    data = data.drop_duplicates(subset=["CellId"], keep="first")
    data = data.reset_index(drop=True)
    data["CellLineId"] = data["CellLineId"].astype(int)

    ############################################
    # Get the mitosis data Labkey
    ############################################
    lk = lkaccess.LabKey(host="aics")
    mito_data = lk.select_rows_as_list(
        schema_name="processing",
        query_name="MitoticAnnotation",
        sort="MitoticAnnotation",
        columns=["CellId", "MitoticStateId", "MitoticStateId/Name", "Complete"],
    )

    mito_data = pd.DataFrame(mito_data)

    # get both binary mitosis labels and resolved (m1, m2, etc) labels

    mito_binary_inds = mito_data["MitoticStateId/Name"] == "Mitosis"
    not_mito_inds = mito_data["MitoticStateId/Name"] == "M0"

    mito_data_binary = mito_data[mito_binary_inds | not_mito_inds]
    mito_data_resolved = mito_data[~mito_binary_inds]

    mito_states = list()
    for cellId in data["CellId"]:
        mito_state = mito_data_binary["MitoticStateId/Name"][
            mito_data_binary["CellId"] == cellId
        ].values
        if len(mito_state) == 0:
            mito_state = "unknown"

        mito_states.append(mito_state[0])

    data["mito_state_binary"] = np.array(mito_states)
    data["mito_state_binary_ind"] = np.array(
        np.unique(mito_states, return_inverse=True)[1]
    )

    mito_states = list()
    for cellId in data["CellId"]:
        mito_state = mito_data_resolved["MitoticStateId/Name"][
            mito_data_resolved["CellId"] == cellId
        ].values
        if len(mito_state) == 0:
            mito_state = "u"

        mito_states.append(mito_state[0])

    data["mito_state_resolved"] = np.array(mito_states)
    data["mito_state_resolved_ind"] = np.array(
        np.unique(mito_states, return_inverse=True)[1]
    )

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

        for column in data.columns:
            if "ReadPath" in column:
                data[column] = [
                    readpath.replace("/allen/programs/allencell/", "./")
                    for readpath in data[column]
                ]
    else:
        raise NotImplementedError(
            "OSes other than Linux and Mac are currently not supported."
        )

    cell_data = data

    ############################################
    # Remove unnecessary columns
    ############################################

    drop_columns = [column for column in cell_data.columns if "FileId" in column] + [
        "StructEducationName",
        "StructureSegmentationAlgorithmVersion",
        "StructureSegmentationFileId",
        "NucleusSegmentationFileId",
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


def _cell_data_to_fov_data(cell_data):
    FOVIds, FOVId_index = np.unique(cell_data["FOVId"], return_index=True)

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


def get_fov_data():
    # returns a datframe where every row is a FOV

    cell_data = get_cell_data()

    return _cell_data_to_fov_data(cell_data)


def get_data(trim_data_flag=False):
    # Returns dataframe containing image paths and metadata for pipeline4
    #
    # trim_data - use a canned subset instead of the complete collection

    cell_data = get_cell_data()

    if trim_data_flag:
        cell_data = trim_data(cell_data, cell_line_ids=[10, 14, 25, 57, 75], n_fovs=10)

    fov_data = _cell_data_to_fov_data(cell_data)

    return cell_data, fov_data


def trim_data_by_cellline(df, cell_line_ids):

    ############################################
    # Return dataset with only rows having cell line ids in the given list
    ############################################
    ids = ["AICS-" + str(id) for id in cell_line_ids]
    return df[df["CellLine"].isin(ids)]


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
            keep_fov_ids.extend(pd.unqiue(list(df_struct["FOVId_rng"])))

    return df[df["FOVId_rng"].isin(keep_fov_ids)]


def trim_data(df, cell_line_ids=[10, 14, 25, 57, 75], n_fovs=10):
    ############################################
    # Trim dataset to contain only the given cell lines, with only the set number of FOVs or less
    # preset cell line IDs are: ER, Fibrillarin (Nucleolus), Golgi, Nucleophosmin (Nucleolus), Alpha Actinin
    # listing of cell lines by ID can be found at: https://www.allencell.org/cell-catalog.html
    ############################################

    cell_line_trim = trim_data_by_cellline(df, cell_line_ids)
    fov_trim = trim_data_by_cellline_fov_count(cell_line_trim, n_fovs)
    return fov_trim
