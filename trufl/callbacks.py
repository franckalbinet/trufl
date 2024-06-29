# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_callbacks.ipynb.

# %% auto 0
__all__ = ['Variable', 'Callback', 'State', 'MaxCB', 'MinCB', 'StdCB', 'CountCB', 'MoranICB', 'PriorCB']

# %% ../nbs/04_callbacks.ipynb 2
from dataclasses import dataclass

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="The weights matrix is not fully connected")

# %% ../nbs/04_callbacks.ipynb 3
from pysal.lib import weights
from pysal.explore import esda
import itertools
import fastcore.all as fc
from fastcore.basics import patch
import numpy as np
from scipy.spatial import KDTree
import geopandas as gpd
from typing import List
from collections.abc import Callable
import rasterio
from rasterio.mask import mask
import pandas as pd
from typing import Type

# %% ../nbs/04_callbacks.ipynb 5
@dataclass
class Variable:
    "State variable"
    name: str
    value: float

# %% ../nbs/04_callbacks.ipynb 6
class Callback(): pass

# %% ../nbs/04_callbacks.ipynb 8
class State:
    def __init__(self, 
                 measurements:gpd.GeoDataFrame, # Measurements data with `loc_id`, `geometry` and `value` columns. 
                 smp_areas:gpd.GeoDataFrame, # Grid of areas/polygons of interest with `loc_id` and `geometry`.
                 cbs:List[Callable], # List of Callback functions returning `Variable`s.
                ): 
        "Collect various variables/metrics per grid cell/administrative unit."
        fc.store_attr()
        self.unsampled_locs = self.smp_areas.index.difference(self.measurements.index)

# %% ../nbs/04_callbacks.ipynb 9
@patch
def get(self:State, 
        loc_id:str, # Unique id of the Point feature
        as_numpy=False # Whether or not to return a list of `Variable` or a tuple of numpy arrays.
       ):
    "Get the state variables as defined by `cbs` for a given location (`loc_id`)."
    variables = self.run_cbs(loc_id)
    if as_numpy:
        return (np.array([v.name for v in variables]), 
                np.array([v.value for v in variables]))
    else:
        return variables

# %% ../nbs/04_callbacks.ipynb 10
@patch
def __call__(self:State, loc_id=None, **kwargs):
    "Get the state variables as defined by `cbs` for all `loc_id`s as a dataframe."
    loc_ids = self.smp_areas.index
    results = [{v.name: v.value for v in self.run_cbs(loc_id)} | {'loc_id': loc_id} for loc_id in loc_ids]
    return pd.DataFrame(results).set_index('loc_id')

# %% ../nbs/04_callbacks.ipynb 11
@patch
def expand_to_k_nearest(self:State, 
                        subset_measurements:gpd.GeoDataFrame, # Measurements for which Variables are computed.
                        k:int=5, # Number of nearest neighbours (possibly belonging to adjacent cells/admin. units to consider).
                       ):
    "Expand measurements of concern possibly to nearest neighbors of surrounding grid cells."
    tree = KDTree(self.measurements.geometry.apply(lambda p: (p.x, p.y)).tolist());
    _, indices = tree.query(subset_measurements.geometry.apply(lambda p: (p.x, p.y)).tolist(), k=k)
    return self.measurements.iloc[indices.flatten()].reset_index(drop=True)

# %% ../nbs/04_callbacks.ipynb 12
@patch
def _flatten(self:State, variables):
    "Flatten list of variables potentially containing both scalar and tuples."
    return list(itertools.chain(*(v if isinstance(v, tuple) else (v,) 
                                  for v in variables)))

# %% ../nbs/04_callbacks.ipynb 13
@patch
def run_cbs(self:State, loc_id):
    "Run Callbacks sequentially and flatten the results if required."
    variables = []
    for cb in self.cbs:
        variables.append(cb(loc_id, self))
    return self._flatten(variables)

# %% ../nbs/04_callbacks.ipynb 15
class MaxCB(Callback):
    "Compute Maximum value of measurements at given location."
    def __init__(self, name='Max'): fc.store_attr()
    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        if loc_id in o.unsampled_locs: return Variable(self.name, np.nan)
        return Variable(self.name, 
                        np.max(o.measurements.loc[[loc_id]].value.values))

# %% ../nbs/04_callbacks.ipynb 16
class MinCB(Callback):
    "Compute Minimum value of measurements at given location."
    def __init__(self, name='Min'): fc.store_attr()
    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        if loc_id in o.unsampled_locs: return Variable(self.name, np.nan)
        return Variable(self.name, 
                    np.min(o.measurements.loc[[loc_id]].value.values))

# %% ../nbs/04_callbacks.ipynb 17
class StdCB(Callback):
    "Compute Standard deviation of measurements at given location."
    def __init__(self, name='Standard Deviation'): fc.store_attr()
    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        if loc_id in o.unsampled_locs: return Variable(self.name, np.nan)
        return Variable(self.name, 
                    np.std(o.measurements.loc[[loc_id]].value.values))

# %% ../nbs/04_callbacks.ipynb 18
class CountCB(Callback):
    "Compute the number of measurements at given location."
    def __init__(self, name='Count'): fc.store_attr()
    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        if loc_id in o.unsampled_locs: return Variable(self.name, np.nan)
        return Variable(self.name, 
                        len(o.measurements.loc[[loc_id]].value.values))

# %% ../nbs/04_callbacks.ipynb 19
class MoranICB(Callback):
    "Compute Moran.I of measurements at given location. Return NaN if p_sim above threshold."
    def __init__(self, k=5, p_threshold=0.05, name='Moran.I', min_n=5): fc.store_attr()

    def _weights(self, measurements):
        w = weights.KNN.from_dataframe(measurements, k=self.k)
        w.transform = "R" # Row-standardization
        return w
        
    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        if loc_id in o.unsampled_locs: return Variable(self.name, np.nan)
        subset = o.measurements.loc[[loc_id]]
        if len(subset) <= self.min_n: return Variable(self.name, np.nan)
        expanded_measurements = o.expand_to_k_nearest(subset, k=self.k)
        moran = esda.moran.Moran(expanded_measurements['value'], self._weights(expanded_measurements))
        return Variable(self.name, moran.I if moran.p_sim < self.p_threshold else np.nan)

# %% ../nbs/04_callbacks.ipynb 20
class PriorCB(Callback):
    "Emulate a prior by taking the mean of measurement over a single grid cell."
    def __init__(self, 
                 fname_raster:str, # Name of raster file
                 name:str='Prior' # Name of the State variable
                ): 
        fc.store_attr()

    def __call__(self, 
                 loc_id:int, # Unique id of an individual area of interest. 
                 o:Type[State] # A State's object
                ): 
        polygon = o.smp_areas.loc[o.smp_areas.reset_index().loc_id == loc_id].geometry
        with rasterio.open(self.fname_raster) as src:
            out_image, out_transform = mask(src, polygon, crop=True)
            mean_value = np.mean(out_image)
        return Variable(self.name, mean_value)
