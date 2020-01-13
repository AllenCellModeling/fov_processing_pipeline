import numpy as np
import pandas as pd


def cell_data_to_summary_table(cell_data):
    # takes a per-cell data table and returns a summary table

    u_workflows = np.unique(cell_data["Workflow"])

    cell_line_summary_table = {}

    for i, u_cell_line in enumerate(np.unique(cell_data.CellLineId)):
        data_cell_line = cell_data[cell_data.CellLineId == u_cell_line]

        cell_line_summary_table[i] = {}
        cell_line_summary_table[i]["CellLineId"] = u_cell_line
        cell_line_summary_table[i]["Clone"] = np.unique(data_cell_line.Clone)
        cell_line_summary_table[i]["Gene"] = np.unique(data_cell_line.Gene)
        cell_line_summary_table[i]["ProteinDisplayName"] = np.unique(
            data_cell_line.ProteinDisplayName
        )
        cell_line_summary_table[i]["Structure Name"] = np.unique(
            data_cell_line.StructureShortName
        )

        cell_line_summary_table[i]["#cells"] = len(data_cell_line)
        cell_line_summary_table[i]["#fovs"] = len(np.unique(data_cell_line.FOVId))

        # breakdown of #FOVs/workflow
        for u_workflow in u_workflows:
            workflow_inds = data_cell_line["Workflow"] == u_workflow

            cell_line_summary_table[i]["{} (#fovs)".format(u_workflow)] = len(
                np.unique(data_cell_line[workflow_inds]["FOVId"])
            )

    cell_line_summary_table = pd.DataFrame.from_dict(cell_line_summary_table).T

    return cell_line_summary_table


def plot_intensity_profiles(
    z_intensity_dict_list: list, save_path: str, channel_to_align_by=None
):
    """
    This is an example object. Use this example for ideas on how to write doc strings, use logging, construct
    objects. This is not an exhaustive example but a decent start.

    Parameters
    ----------
    im: np.array
        CYXZ image

    Returns
    -------
    stats_dict: dict
        Dictionary containing z_profile information for each channel
    """
