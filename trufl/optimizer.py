# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_optimizer.ipynb.

# %% auto 0
__all__ = ['Optimizer']

# %% ../nbs/02_optimizer.ipynb 2
import numpy as np
from fastcore.basics import patch
from nbdev.showdoc import *
from .mcdm import score, normalize, weigh

# %% ../nbs/02_optimizer.ipynb 3
class Optimizer:
    def __init__(self, state):
        "Optimize the number of points for t. Provided the number of points to sample in t based on t-1, return values number of sample points."
        self.state = state
        
        self.matrix = state.to_numpy()
        return

# %% ../nbs/02_optimizer.ipynb 4
@patch
def get_rank(self:Optimizer, is_benefit_x:list, w_vector:list,  
         n_method:str=None, c_method:str = None, 
         w_method:str=None, s_method:str=None):
    
    # normailize the matrix
    z_matrix, is_benefit_z = normalize(self.matrix, is_benefit_x, n_method)
    
    if w_vector is None:
            # Weigh each criterion using the selected methods
            w_vector = weigh(z_matrix, w_method, c_method)
    else:
        pass

    s_vector, desc_order = score(z_matrix, is_benefit_z, w_vector, s_method)
    self.state['value'] = s_vector
    df = self.state[['value']]

    # Get the indices of the sorted scores
    if desc_order:
        df_sorted = df.sort_values(by='value', ascending=False)
    else:
        df_sorted = df.sort_values(by='value', ascending=True)
    
    df_sorted['rank'] = range(1, len(df_sorted) + 1)
    df_rank = df_sorted[['rank']]
    
    return df_rank
