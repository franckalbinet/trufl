# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_sampler.ipynb.

# %% auto 0
__all__ = ['Sampler']

# %% ../nbs/01_sampler.ipynb 3
import rasterio
import fastcore.all as fc
import geopandas as gpd
import numpy as np

# %% ../nbs/01_sampler.ipynb 5
class Sampler:
    "Sample random location in `smp_areas`."
    def __init__(self, 
                 smp_areas:gpd.GeoDataFrame, # Geographical area to sample from.
                ) -> gpd.GeoDataFrame: # loc_id, geometry (Point or MultiPoint).
        fc.store_attr()
        
    @property
    def loc_ids(self):
        arr = self.smp_areas.reset_index().loc_id.values
        if len(arr) != len(np.unique(arr)):
            raise ValueError(f'{self.loc_id_col} column contains non-unique values.')
        else:
            return arr
        
    def sample(self, 
               n:np.ndarray, # Number of samples
               **kwargs
              ):
        mask = n == 0    
        pts_gseries = self.smp_areas[~mask].sample_points(n[~mask], **kwargs)
        gdf_pts = gpd.GeoDataFrame(geometry=pts_gseries, index=pts_gseries.index)
        gdf_pts.index.name = 'loc_id'
        return gdf_pts
