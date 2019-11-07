import lkaccess
import lkaccess.contexts
import pandas as pd
import numpy as np
from sys import platform

from .utils import int2rand


def get_cell_data(is_local=False):
    # TODO
    # remove unnecessary column from dataframe

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
    if is_local:
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

    drop_columns = [
        "StructureSegmentationFileId",
        "NucleusSegmentationFileId",
        "StructEducationName",
    ]
    drop_columns = [column for column in cell_data.columns if "FileId" in column] + [
        "StructEducationName",
        "StructureSegmentationAlgorithmVersion",
    ]

    cell_data = cell_data.drop(drop_columns, axis=1)

    ############################################
    # Assign random numbers to IDs
    ############################################

    id_columns = [column for column in cell_data.columns if column[-2:] == "Id"]

    for id_column in id_columns:
        try:
            cell_data["{}_rng".format(id_column)] = [
                int2rand(my_id) for my_id in cell_data[id_column]
            ]
        except:
            import pdb
            pdb.set_trace()

    return cell_data


def cell_data_to_fov_data(cell_data):
    FOVIds, FOVId_index = np.unique(cell_data["FOVId"], return_index=True)

    fov_data = cell_data.iloc[FOVId_index]

    # Drop any columns that are per-cell information
    drop_columns = [
        column
        for column in fov_data.columns
        if ("cell" in column.lower()) | ("mito" in column.lower())
    ]

    fov_data = fov_data.drop(drop_columns, axis=1)

    raise fov_data


def get_fov_data(is_local=False):
    cell_data = get_cell_data(is_local)

    return cell_data_to_fov_data(cell_data)

