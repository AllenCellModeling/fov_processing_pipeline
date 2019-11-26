import numpy as np


def fov_qc(df):
    """
    Given a stats dataframe, check for any FOV's that have their brightest average zslice DNA intensity at the bottom.
    This is an indicator of a slice being out of order, and we want to QC these out of our list.
    Parameters
    ----------
    df: Dataframe
        Stats dataframe, with rows corresponding to FOVs and a column for the mean DNA intensity, for each zslice
    Returns
    -------
    df: Dataframe
        Same dataframe, with aberrant FOVs removed
    """
    qc = []

    for i in range(df.shape[0]):
        vals = df.iloc[i]['Ch1_mean_by_z']
        ind = np.argmax(vals)
        qc.append(ind != 0)

    df['QC'] = qc
    return df[df['QC']]


def zsize_qc(df):
    """
    Given a stats dataframe, use interpolation to make sure all zslice data has the same number of z measurements
    Parameters
    ----------
    df: Dataframe
        Stats dataframe, with rows corresponding to FOVs and a column for the mean DNA intensity, for each zslice
    Returns
    -------
    df: Dataframe
        Same dataframe, with stats interpolated so that all FOV stats now match in z-size
    """

    # get median number of z slices
    z_sizes = [len(df.iloc[i]['Ch0_mean_by_z']) for i in range(df.shape[0])]
    set_size = int(np.median(z_sizes))

    # cycle through channels to make a new list of values for each channel
    for ch in range(4):
        means = []
        stds = []

        col1 = 'Ch'+str(ch)+'_mean_by_z'
        col2 = 'Ch'+str(ch)+'_std_by_z'

        # for every fov, interpolate z intensity mean and std to same size
        for i in range(df.shape[0]):

            # get z size and check if it equals the size we are standardizing to
            z_size = len(df.iloc[i, df.columns.get_loc(col1)])

            # if already correct size, just add the original values
            if z_size == set_size:
                means.append(df.iloc[i][col1])
                stds.append(df.iloc[i][col2])

            # if not already right size, interpolate a new array and add the interpolated array
            else:

                old_zinds = range(z_size)
                new_zinds = range(set_size)

                # interpolate mean values
                old_vals = df.iloc[i, df.columns.get_loc(col1)]
                new_vals = np.interp(new_zinds, old_zinds, old_vals)
                means.append(new_vals)

                # interpolate std values
                old_vals = df.iloc[i, df.columns.get_loc(col2)]
                new_vals = np.interp(new_zinds, old_zinds, old_vals)
                stds.append(np.interp(new_zinds, old_zinds, old_vals))

        # reset channel values to new list of values
        df = df.drop(col1, axis=1)
        df = df.drop(col2, axis=1)
        df[col1] = means
        df[col2] = stds

    return df
