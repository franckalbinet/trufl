# Roadmap

Small next steps, then open questions about where trufl goes next. The questions don't all need answers now: a question becomes an issue once it is settled enough to be done in one commit.

## Next steps

Each step fits in one commit.

- Per-unit table for one campaign: for each decision unit, the true mean and maximum from the raster, the measured mean and maximum, the number of samples and the Wasserstein distance. Units with no samples show as empty rows. No weighting, reference allocations or masks yet. Try it on the multi-year how-to before deciding what a score should be (#12).
- Prior from a degraded copy of the ground truth, so simulated campaigns stop using a perfect prior (#11).
- Fix `anonymize_raster`, which raises `NameError` on every call because its body uses `src_fname` and `dst_fname`, which are not parameters (#10).

## The campaign as a sequence of steps

- Is a round best described as five steps: describe the state of each decision unit, rank the units, allocate the budget, place the samples within each unit, and measure?
- Should the documentation be organised around these steps?

## Units and placement

- Decisions are made per administrative unit, such as a municipality. Where within such a unit should samples go?
- Is a grid finer than the administrative units a useful way to stratify samples within them?
- How should masks restrict placement, for example to one land use, or away from areas too contaminated to send people into?
- Which restrictions are hard constraints that remove options, such as keeping people out of a zone, and which are soft costs that the ranking can trade off, such as travel time? Should hard constraints act before ranking: on allocation when they exclude a whole unit, and on placement when they exclude part of one?
- Which placement methods besides uniform random sampling are worth having?

## Criteria

- Which criteria other than contamination, such as economic value, population or land use, are useful?
- How can trufl work with as few inputs as possible, and add others when they become available?

## Scoring a campaign

- How should we measure what a campaign knows about each unit compared with the ground truth? Is the Wasserstein distance a good measure?
- How do we avoid a measure that rewards samples for missing a small hotspot?
- How do we score a unit that nobody sampled?
- With a mask, do we judge what is known about the whole unit, or only about the part that can be sampled?
- How should the scores of units be combined, and should some units count more than others?
- How do we tell whether a score is good, for example compared with random allocation, or with the best allocation possible when the truth is known?

## Comparing strategies

- When is it better to spend the budget early, and when over several rounds?
- How should the minimum number of samples per unit be handled when schedules have different numbers of rounds?
- How much does a strategy depend on the quality of the prior?
- How do samples taken without planning affect a strategy?
- How does trufl compare with textbook methods, such as Neyman allocation?

## Ground truths

- How do we build many ground-truth rasters, and how do we pick prototypical ones?
- Can a ground truth derived from Fukushima data be used and published?

## Interpolated surfaces

- How should surface metrics from interpolation, such as IDW or kriging, deal with the choice of their parameters?

## Literature

- Where does trufl sit in the literature on adaptive and stratified spatial sampling, multi-phase surveys and multiple-criteria decision-making?
