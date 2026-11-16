# Scoring plan

Working plan for scoring a sampling campaign against the ground truth (#12). Still to be refined.

## First step

Build a per-unit table for one campaign, as the roadmap's next step describes. For each decision unit:

- the true mean and maximum, from the raster cells inside the unit
- the measured mean and maximum, from the samples
- the number of samples
- the Wasserstein distance between the raster cell values and the sample values

Units with no samples have a count of 0 and empty values for the rest. No weighting, reference allocations or masks yet.

Try the table on the multi-year how-to before deciding what a score should be.

## Implementation

- Experiment in `nbs/07_scoring.ipynb`. It becomes the `trufl.scoring` module once the design settles.
- Samples from `DataCollector.collect` are indexed by `loc_id` and hold a `value` column, so the measured statistics come from a group-by.
- Use `scipy.stats.wasserstein_distance`.
- Add `scipy` to the dependencies in `pyproject.toml`. `callbacks` already imports it directly, but it arrives only through `pysal`.
- Read the true values with `trufl.utils.zonal_values`, which `PriorCB` also uses. It counts a cell whose centre lies exactly on a unit border in both units. Only `gridder` grids whose units are not a whole number of cells wide have such borders: on `ground-truth-02`, 1,376 of 705,200 cells are counted twice. Rounding `gridder` units to whole cells would remove the double count.

## Open questions

- How should the true values be weighted or normalised in the Wasserstein distance? In practice the ground truth may be polygons of different sizes, such as agricultural fields, rather than raster cells of equal size. On a raster, weights could come from cell area or from the share of a cell inside the unit. On the simulated raster, cell areas differ by 0.15% at most. `wasserstein_distance` takes weights for both distributions.
- Should the how-to keep the per-year tables on its page, or should the scoring notebook run its own campaign?

## Later

From #12, once the table has been tried:

- Hotspot detection: for each unit with hotspot cells, did its samples find one?
- Hotspot coverage: the share of hotspot cells within a given distance of a sample.
- Surface metrics from interpolation (IDW first), compared with the raster cell by cell.
