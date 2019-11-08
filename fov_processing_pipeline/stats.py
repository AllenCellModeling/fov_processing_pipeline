import numpy as np

def z_intensity_stats(im, c):
    ############################################
    # For a given channel and image, calculate stats for the intensity as a function of z slice:
    #   - Mean intensity
    #   - Standard deviation of intensity
    ############################################
    nz = im.shape[3]

    meanc = np.empty(nz)
    stdc = np.empty(nz)

    for z in range(im.shape[3]):
        imc_vals = im[c, :, :, z].flatten()
        meanc[z] = np.mean(imc_vals)
        stdc[z] = np.std(imc_vals)

    clabel =  'Ch'+str(c)+'_'
    zlabel = '_by_z'
    return {clabel+'mean'+zlabel: meanc,  clabel+'std'+zlabel: stdc}



def intensity_percentiles_by_channel(im, c, percentile_list=[5, 25, 50, 75, 95]):
    ############################################
    # For each channel of an image, calculate the percentile intensity values in list
    ############################################
    results = dict()
    imvals = im[c, :, :, :].flatten()
    for p in percentile_list:
        results.update({'Ch'+str(c)+'_Percentile'+str(p): np.percentile(imvals, p)})
    return results