# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_callbacks.ipynb.

# %% auto 0
__all__ = ['Variable', 'Callback', 'State', 'MaxCB', 'MinCB', 'StdCB', 'CountCB', 'MoranICB']

# %% ../nbs/04_callbacks.ipynb 2
from dataclasses import dataclass

# %% ../nbs/04_callbacks.ipynb 3
from pysal.lib import weights
from pysal.explore import esda
import itertools
import fastcore.all as fc
import numpy as np
from scipy.spatial import KDTree

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="The weights matrix is not fully connected")

# %% ../nbs/04_callbacks.ipynb 6
@dataclass
class Variable:
    "State variable"
    name: str
    value: float

# %% ../nbs/04_callbacks.ipynb 7
class Callback(): pass

# %% ../nbs/04_callbacks.ipynb 8
class State:
    def __init__(self, measurements, cbs): fc.store_attr()
        
    def get(self, loc_id, as_numpy=False):
        variables = self.run_cbs(loc_id)
        if as_numpy:
            return (np.array([v.name for v in variables]), 
                    np.array([v.value for v in variables]))
        else:
            return variables

    def expand_to_k_nearest(self, subset_measurements, k=5):
        tree = KDTree(self.measurements.geometry.apply(lambda p: (p.x, p.y)).tolist());
        _, indices = tree.query(subset_measurements.geometry.apply(lambda p: (p.x, p.y)).tolist(), k=k)
        return self.measurements.iloc[indices.flatten()].reset_index(drop=True)
        
    def _flatten(self, variables):
        "Flatten list of variables potentially containing both scalar and tuples."
        return list(itertools.chain(*(v if isinstance(v, tuple) else (v,) 
                                      for v in variables)))
    def run_cbs(self, loc_id):
        variables = []
        for cb in self.cbs:
            variables.append(cb(loc_id, self))
        return self._flatten(variables)

# %% ../nbs/04_callbacks.ipynb 9
class MaxCB(Callback):
    def __call__(self, loc_id, state): 
        return Variable(
            'Max', 
            np.max(state.measurements[state.measurements.loc_id == loc_id]['value'].values))

# %% ../nbs/04_callbacks.ipynb 10
class MinCB(Callback):
    def __call__(self, loc_id, state): 
        return Variable(
            'Min', 
            np.min(state.measurements[state.measurements.loc_id == loc_id]['value'].values))

# %% ../nbs/04_callbacks.ipynb 11
class StdCB(Callback):
    def __call__(self, loc_id, state): 
        return Variable(
            'Standard Deviation', 
            np.std(state.measurements[state.measurements.loc_id == loc_id]['value'].values))

# %% ../nbs/04_callbacks.ipynb 12
class CountCB(Callback):
    def __call__(self, loc_id, state): 
        return Variable(
            'Count', 
            len(state.measurements[state.measurements.loc_id == loc_id]['value'].values))

# %% ../nbs/04_callbacks.ipynb 13
class MoranICB(Callback):
    def __init__(self, k=5): fc.store_attr()

    def _weights(self, measurements):
        w = weights.KNN.from_dataframe(measurements, k=self.k)
        w.transform = "R" # Row-standardization
        return w
        
    def __call__(self, loc_id, state): 
        subset = state.measurements[state.measurements.loc_id == loc_id];
        expanded_measurements = state.expand_to_k_nearest(subset, k=self.k)
        moran = esda.moran.Moran(expanded_measurements['value'], self._weights(expanded_measurements))
        return Variable('Moran.I', moran.I), Variable('Moran_p_sim', moran.p_sim)
