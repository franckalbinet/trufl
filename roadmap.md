# Roadmap

Open questions about where trufl goes next. A question becomes an issue once it is settled enough to be done in one commit.

## The campaign as a sequence of steps

- Is a round best described as five steps: describe the state of each decision unit, rank the units, allocate the budget, place the samples within each unit, and measure?
- Should the documentation be organised around these steps?

## Units and placement

- Decisions are made per administrative unit, such as a municipality. Where within such a unit should samples go?
- Is a grid finer than the administrative units a useful way to stratify samples within them?
- How should masks restrict placement, for example to one land use, or away from areas too contaminated to send people into?
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
