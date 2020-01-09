import pandas as pd
import numpy as np

from . import utils as data_utils


def get_cell_data():
    # returns a datframe where every row is a cell

    # Move this to top-level imports if/when lkaccess becomes open source
    import lkaccess
    import lkaccess.contexts

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

    return data


def get_data(n_fovs=100, protein_list=None):

    # Returns dataframe containing image paths and metadata for pipeline4
    #
    # trim_data - use a canned data subset

    cell_data = get_cell_data()

    cell_data, fov_data = data_utils.clean_cell_data(cell_data, protein_list=protein_list, n_fovs=n_fovs)

    return cell_data, fov_data
