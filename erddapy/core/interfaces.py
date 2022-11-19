"""
Interface between URL responses and third-party libraries.

This module takes an URL or the bytes response of a request and converts it to Pandas,
XArray, Iris, etc. objects.
"""
from typing import TYPE_CHECKING

from typing import Dict

import pandas as pd

from erddapy.core.netcdf import _nc_dataset, _tempnc
from erddapy.core.url import urlopen

if TYPE_CHECKING:
    import xarray as xr
    from netCDF4 import Dataset

def to_pandas(url: str, requests_kwargs: Dict = None, **kw) -> "pd.DataFrame":
    """
    Convert a URL to Pandas DataFrame.

    url: URL to request data from.
    requests_kwargs: arguments to be passed to urlopen method.
    **kw: kwargs to be passed to third-party library (pandas).
    """
    if requests_kwargs is None:
        requests_kwargs = {}
    data = urlopen(url, **requests_kwargs)
    try:
        return pd.read_csv(data, **kw)
    except Exception as e:
        raise ValueError(f"Could not read url {url} with Pandas.read_csv.") from e


def to_ncCF(url: str, protocol: str = None, **kw) -> "Dataset":
    """Convert a URL to a netCDF4 Dataset."""
    if protocol == "griddap":
        raise ValueError(
            f"Cannot use .ncCF with griddap protocol. The URL you tried to access is: '{url}'.",
        )
    auth = kw.pop("auth", None)
    return _nc_dataset(url, auth=auth, **kw)


def to_xarray(
    url: str, response="opendap", requests_kwargs: Dict = None, **kw
) -> "xr.Dataset":
    """
    Convert a URL to an xarray dataset.

    url: URL to request data from.
    response: type of response to be requested from the server.
    requests_kwargs: arguments to be passed to urlopen method.
    **kw: kwargs to be passed to third-party library (xarray).
    """
    import xarray as xr

    auth = kw.pop("auth", None)
    if response == "opendap":
        return xr.open_dataset(url, **kw)
    else:
        if requests_kwargs is None:
            requests_kwargs = {}
        nc = _nc_dataset(url, auth=auth, **requests_kwargs)
        return xr.open_dataset(xr.backends.NetCDF4DataStore(nc), **kw)


def to_iris(url: str, requests_kwargs: Dict = None, **kw):
    """
    Convert a URL to an iris CubeList.

    url: URL to request data from.
    requests_kwargs: arguments to be passed to urlopen method.
    **kw: kwargs to be passed to third-party library (iris).
    """
    import iris

    if requests_kwargs is None:
        requests_kwargs = {}
    data = urlopen(url, **requests_kwargs)
    with _tempnc(data) as tmp:
        cubes = iris.load_raw(tmp, **kw)
        _ = [cube.data for cube in cubes]
        return cubes
