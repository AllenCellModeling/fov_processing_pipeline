def check_input(im, channel_names=None, ndims=None):
    """
    Image checker for stats functions

    Parameters
    ----------
    im: np.array
        image with "ndims" dimensions

    channel_names: list
        list of names corresponding to each channel, or None

    ndims: int
        desired dimensonality of the input, or None

    Returns
    -------
    channel_names: list
        list of names corresponding to each channel

    """

    if ndims:
        if len(im.shape) != ndims:
            raise ValueError("Must have a {}D input".format(ndims))

    if not channel_names:
        channel_names = ["Ch{}".format(i) for i in range(im.shape[0])]

    if im.shape[0] != len(channel_names):
        raise ValueError(
            "If channel_names is defined it must be the same length as the number of channels in the image"
        )

    return channel_names
