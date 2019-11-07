import aicsimagio


def row2img(df_row):
    # take a dataframe row and returns an image in CZYX format with channels in order of
    # Brightfield, DNA, Membrane, Structure, seg_dna, seg_membrane, seg_structure
    raise NotImplementedError


def im2stats():
    # takes a FOV and returns some basic statistics
    raise NotImplementedError
