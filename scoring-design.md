# Scoring and allocation: design proposal

Status: proposal for discussion. Nothing here is decided. The evidence is in `scoring-plan.md`, and the code in `nbs/07_scoring.ipynb` and `nbs/_scoring_experiments.ipynb`.

## Summary

trufl would allocate samples so that decision makers' decisions are right, not so that every unit is described equally well. Four parts, each with one job:

- A decision rule, given as input: the rule decision makers apply to a unit's samples, such as the DSS4NAFA restriction rule.
- An information layer: it allocates each round's budget where samples most lower the expected number of wrong decisions under that rule. `voi` is the current version.
- A value layer: MCDM, as today, but on value criteria only (population, production, economic value), giving each unit a weight for what is at stake there.
- A simulation module: campaigns over a ground truth, strategies and scores, to compare strategies before an emergency.

## Evidence

From `scoring-plan.md`, wrong restriction decisions after six rounds of 150 samples, 20 seeds:

- On `ground-truth-02` at a level of 0.473: 10.0 with equal allocation, 7.8 with `bayes`, 4.0 with `voi` and a perfect prior.
- On three windows of the 2011 Fukushima raster, `bayes` beats equal allocation in all six settings, and the how-to MCDM strategy in five.
- Scored on the error of unit means instead of decisions, no strategy beats equal allocation. MCDM was scored on a job it was not designed for.
- A prior helps only when the allocation predicts the decision the rule will make from the samples (`voi`). With `bayes`, which trusts the prior, even a perfect prior makes decisions worse.
- With realistic priors, `voi` gains only if the prior's weight matches its quality: a poor prior with too much weight does worse than equal allocation.

## Decision rule

A decision rule takes a unit's sample values and returns an action: `restrict`, `no restrict`, `sample` (too few samples) or `undefined` (no samples). The first rule is the DSS4NAFA rule with three settings: permissible level, minimum number of samples and accepted proportion over the level. A sample counts as above when it is strictly above the level, and the unit is restricted when the share of samples above is at least the accepted proportion (`suggestRestriction` in the dashboard's `app-model.js`). With 10%, one exceedance in 10 samples restricts. Results recorded before this was checked used "more than" and are one exceedance off at the boundary.

The information layer needs more than the action. To predict a future decision, it needs the number of exceedances the rule requires for each number of samples. Proposed: a small class per rule, for example `ShareRule(level, accepted, min_n)`, with `decide(values)` and `needed(n)`. `expected_wrong` then works for any rule that decides on a count of exceedances. A rule on the measured values themselves (see the sawtooth in `nbs/_explain_04_sawtooth.ipynb`) would need a different `expected_wrong`.

### Is the share rule the right criterion?

The experiments point at the DSS4NAFA rule itself, not only at the sampling:

- The sawtooth: because the rule counts exceedances, one more sample can make a decision less reliable, and stopping at 10 samples beats taking an 11th.
- The rule ignores how far values are above or below the level. A sample at 1.1 times the level counts the same as one at 10 times. A rule on the measured values has no sawtooth (`nbs/_explain_04_sawtooth.ipynb`).
- The rule ignores prior information such as the airborne survey, which is why a prior made `bayes` worse.
- Part of the perverse incentive of costs ("Health as a limit") comes from the rule. Any rule changes a decision only by flipping it, but under a rule that converges, the chance of a wrong flip falls steadily with more samples. Under the share rule it jumps, which makes sampling look risky where a restriction is expensive.

The rule also has strengths: it is transparent, needs no model of how contamination is distributed, and is easy to defend. A replacement would give up some of that.

The share of a unit's area above the level is a proxy. What decision makers want to control is more likely the dose to consumers, which depends on concentrations and consumption, weighed against the harm of restricting. Candidate rules: restrict when the probability that the share exceeds the accepted proportion is above a confidence level, which makes precaution an explicit setting; or decide on an upper bound of the mean concentration.

trufl takes the rule as an input, so it can compare rules without choosing one. The scoring defines the true action through the share above the level, the same criterion as the current rule. A fair comparison of rules needs a truth that no rule defines, such as each unit's true dose or true share, scored on the synthetic plumes. That would give DSS4NAFA evidence for the choice. Nothing here is decided.

### How decisions are made in practice

After Fukushima, Japan did not use a share rule. The rules come from the Nuclear Emergency Response Headquarters guideline "Concepts of Inspection Planning and the Establishment and Cancellation of Items and Areas to which Restriction on Distribution and/or Consumption of Foods Concerned Applies" (April 2011, revised often since):

- A local government removes any food item found above the limit from the market. When "extensive areas are found to be affected", the Prime Minister, as head of the Headquarters, restricts distribution of the item in the designated regions. When levels are high, consumption is restricted "irrespective of the number of inspected samples". The guideline does not set a share or a count of exceedances; whether an area is affected is a judgement. (Ministry of the Environment booklet, section 8.1.1.)
- A restriction is lifted when inspections at 3 or more locations per municipality within the last month are all below the limit. (MHLW press release, March 2021.)
- The limits for radiocaesium came into force on 1 April 2012: 100 Bq/kg for general foods, 50 for milk and infant foods, 10 for drinking water. They replaced the provisional values of 2011 (500 Bq/kg for general foods), which assumed 5 mSv per year from food; the new ones assume 1 mSv per year. The numbers are from memory; the sources found confirm the dates and the dose basis only.
- Measured values counted, not only exceedances. In April 2011, rice planting was banned in paddies with more than 5,000 Bq/kg of caesium in soil, from a transfer factor of 0.1 (the highest found in the literature) and the 500 Bq/kg limit. (Secondary sources and MAFF slides; the original MAFF notice was not found.)
- From 2012 to 2019, Fukushima measured every bag of rice with conveyor-type meters, then moved to staged random monitoring from the 2020 harvest. No rice has exceeded the limit since 2015. (Ministry of the Environment booklet, section 8.2.)

Sources:

- Ministry of the Environment, booklet on health effects of radiation, [section 8.1.1](https://www.env.go.jp/en/chemi/rhm/basic-info/2022/08-01-01.html), [section 8.1.3](https://www.env.go.jp/en/chemi/rhm/basic-info/2022/08-01-03.html), [section 8.2.1 (rice)](https://www.env.go.jp/en/chemi/rhm/basic-info/2023/08-02-01.html) and [the Concepts guideline](https://www.env.go.jp/en/chemi/rhm/basic-info/1st/08-01-15.html).
- MHLW, [revision of the Concepts, March 2021](https://www.mhlw.go.jp/english/topics/2011eq/dl/food_revision_26%20March_2021.pdf) and [March 2026](https://www.mhlw.go.jp/english/topics/2011eq/dl/food_revision_30_March_2026.pdf).
- MAFF, [response to the accident](https://www.maff.go.jp/e/policies/food_safety/attach/pdf/response-1.pdf).
- IAEA, [slides on the rice transfer factor](https://www.iaea.org/sites/default/files/21/07/_t2_01_iaea_shinano.pdf).

This is close to a maximum rule: exceedances restrict, and only consistent clean results lift a restriction. A maximum rule is a candidate for the comparison of rules.

In DSS4NAFA, the rule's three settings (permissible level, minimum number of samples, accepted proportion) are rigid, and the dashboard only suggests an action. Analysts and decision makers make the decision. They can change the settings and look at the data themselves: the values, their spatial distribution and other information. The suggested action is one input among several.

The optimization in this design targets only the suggested action under the share rule. It does not target what the people deciding look at, such as the values, the maps or the uncertainty of a unit's mean. This is a gap. Options include scoring strategies against several rules at once, or against how well a strategy estimates the quantities shown on the dashboard. Nothing here is decided.

## Information layer

A strategy is a function `(samples, gdf_units, budget, rng) -> n`, giving the number of samples for each unit in `gdf_units` order. The proposed public strategy is `voi(rule, min_total, prior, strength, horizon)`:

- It tops each unit up to `min_total` samples over the whole campaign. This is the dashboard's minimum number of samples, a decision makers' setting.
- It gives each remaining sample to the unit with the largest drop of `expected_wrong` per sample over the next 1 to `horizon` samples (10 by default; 5 left needless restrictions in place, see the plume evidence).
- `prior` is an optional raster, such as an airborne survey, and `strength` the number of samples it is worth.

With a value layer, the gain of each unit is multiplied by its stake weight, so a sample goes where it most lowers the stake-weighted number of wrong decisions. With no value layer, every weight is 1.

`allocate` (proportional allocation after a minimum) is a shared helper. `bayes`, `equal` and `neyman` are baselines, and stay in the simulation module.

## Placement within a unit

Where samples go inside a unit matters as much as how many each unit gets, once the field is spatially correlated. Proposed: placement as a part next to the information layer. Nothing here is decided.

The binomial model in `bayes` and `voi` assumes samples placed uniformly at random within the unit. Then each sample is above the level with probability equal to the share of the unit's area above it, whatever the spatial pattern, so the model is exact. It does not assume an uncorrelated field.

Evidence, from "Placement within a unit" in `nbs/_scoring_experiments.ipynb`: synthetic Gaussian random fields on one unit, 1,000 fields per setting, correlation set by a smoothing width `sigma` (16 cells is 1/8 of the unit width):

- Random placement gives the binomial error whatever the correlation.
- At `sigma` 16, a systematic grid of 16 samples estimates the share about as well as 49 random samples; 36 as well as about 150; 64 as well as about 400.
- At `sigma` 16 and a true share of 12%, 64 random samples give a wrong decision 38% of the time, and 64 systematic samples 12%.
- Clustered placement (4 clusters, as when teams sample near roads or one farm) is wrong 56 to 58% of the time at 12%, and more samples don't help. Most clusters miss the patch, so the errors are missed restrictions.
- With no correlation, all placements are the same.

What it would change:

- Recommend a systematic or stratified layout within each unit. It costs no extra samples. Without correlation it matched random placement within simulation noise, and with correlation it did better.
- In `voi`, replace each unit's sample count by an effective count that depends on the placement and on the correlation range relative to the unit size. Without it, `voi` overspends on spread units and is overconfident on clustered ones.
- Estimate the correlation range from a variogram or the scale of the prior raster. Moran's I from a unit's samples shows whether correlation is present, but not its range.
- With strong correlation, the exceedances form a patch, which makes "partially restrict" meaningful and opens adaptive placement near the first exceedances.

### Directional fields and plumes

After an accident, contamination follows the plume. That gives two effects. Within a unit, the correlation is anisotropic: a long range along the plume and a short one across it. Between units, there is a trend: values fall with distance from the source and away from the plume axis, so decisions are close only along the plume edge. The usual model is `log value = trend + correlated residual`, with the trend from a dispersion model or the airborne survey. Nothing here is decided.

Evidence, from "Directional fields", "A synthetic plume", "Placement in the plume" and "Replication over plumes" in `nbs/_scoring_experiments.ipynb` (synthetic fields only), rerun with the dashboard's rule of at least 10% of samples above the level:

- Within a unit (36 samples, 2,000 fields per setting), strata stretched along the plume, by rotating the coordinates to the plume axis and dividing by the range in each direction, are worth about 10 more samples than square strata when the anisotropy is strong (ranges 2 by 32 cells), and 1 to 7 more when it is mild (4 by 16). Stretched along the wrong axis, they lose most of the gain from stratifying. Square strata are the safe choice when the direction is uncertain.
- Between units (a synthetic Gaussian plume over 10 by 10 units, 40 seeds, wrong decisions after round 6): `voi` with a survey or perfect prior 3.6 to 5.2, with a dispersion-model prior at strength 4 5.2, with no prior 5.7, equal allocation 6.0. At strength 4 the survey prior does no better than the dispersion prior (5.2 each). With the wind 10° off, the dispersion prior at strength 4 gives no gain (5.6). At strength 20, both dispersion priors are worse than equal allocation (9.2 and 8.5), because the trend lacks the residual patches.
- Placement in the plume (`Campaign(placement=...)`, five strategies, 40 seeds): against uniform placement, `spread` along the plume lowers wrong decisions after round 6 by about 0.8 on average over the strategies, `spread` in every direction by about 0.4, and the wrong axis by about 0.3 (differences between means; standard errors up to 0.34). `voi` with the dispersion prior and spread along the plume makes 4.6 wrong decisions, fewer than `voi` with the survey prior and uniform placement (5.2).
- Replication over ten plume fields (own seed, wind angle, spread and residual strength; seven strategies, three placements, 20 seeds each), differences between fields: the survey prior at strength 4 lowers wrong decisions against `voi` with no prior by 0.81 ± 0.26 (7 of 10 fields) and the dispersion prior by 0.46 ± 0.22 (7 of 10); with the wind 10° off, the dispersion prior gives no gain (0.09 ± 0.22). Spread placement is not confirmed: averaged over strategies, `spread` lowers wrong decisions by 0.35 ± 0.33 and `spread` along the plume by 0.38 ± 0.36, each in 5 of 10 fields (before the rule change, 0.51 ± 0.25 and 0.63 ± 0.31). `bayes` and `voi` with the dispersion prior at strength 20 gain most from spreading along the plume (5.15 to 3.99 and 6.73 to 5.36); `voi` with no prior gains 0.09. The dispersion prior at strength 20 is worse than equal allocation by 0.91 ± 0.56, in 6 of 10 fields. `voi` and `bayes` do not differ (0.02 ± 0.24).
- `voi`'s horizon ("Diagnosis" and "`voi`'s horizon" in the experiments notebook): with a horizon of 5, `voi` stopped sampling units with an early exceedance, such as 1 of 3 above the level, because the measured share drops below 10% only after 8 more clean samples. These became needless restrictions. Over the ten plume fields, a horizon of 10 lowers wrong decisions for 8 of the 9 pairs of strategy and placement, by 0.4 to 2.0, more with spread placement than without. It also raises missed restrictions by 0.15 to 1.8. With horizon 10 and spread placement, `voi` with the survey prior makes 2.7 wrong decisions and with the dispersion prior 3.2 to 3.5, the fewest of the realistic strategies tested. The default `horizon` in `nbs/07_scoring.ipynb` is now 10.

What it would change:

- Placement: spread samples away from a unit's earlier samples. Across rounds this needs a placement such as `spread` in `nbs/07_scoring.ipynb` (best-candidate sampling), because strata built each round hold one or two samples. Over ten plumes, stretching the distances along the plume added little to spreading in every direction (the means differ by 0.03). It may matter more with stronger anisotropy or larger units, which is not tested.
- Priors: a dispersion model can serve as `voi`'s prior before a survey exists, with a small weight (about 4 samples). Over ten plumes it lowered wrong decisions in 7, and a weight of 20 was harmful on some plumes. A survey, once available, is the better prior.
- Decisions: a unit cut by the plume edge is the clearest case for "partially restrict", and the trend gives the line along which to split it.
- Publication: the synthetic plume is a candidate ground truth that resembles a real accident without using Fukushima data.

## Value layer

`Optimizer`, `State` and the callbacks keep their role of ranking units, on value criteria. The proposed change is in what they are used for: they give `voi` weights per unit instead of deciding the allocation themselves through `rank_to_sample`. With two costs per unit, they give two weights, one for each kind of wrong decision (see "Costs from MCDM" under "Dilemmas").

Two open points:

- How a rank becomes a weight. A rank loses the size of the differences between units; the `CP` or `TOPSIS` score keeps it. Proposed: use the score, rescaled to [0, 1].
- Whether the information criteria (`StdCB`, `CountCB`, `MoranICB`) stay in the recommended path. With `voi` handling information, they are not needed for allocation. They stay in the library for existing users.

## Dilemmas

A nuclear response weighs one harm against another. Economic value against health risk is one example. This section lists the dilemmas found so far, and what each one would change in trufl. Nothing here is decided.

### Two costs per unit

Today `voi` counts every wrong decision as 1, and the value layer proposes one stake weight per unit. A needless restriction and a missed restriction have different stakes. The cost of a needless restriction grows with what the restriction destroys, such as the economic value of a crop. The cost of a missed restriction grows with the risk to consumers. Proposed: two weights per unit, from the value layer, and `voi` lowers the expected cost:

    expected cost = c_needless * P(needless restriction) + c_missed * P(missed restriction)

Example: a field with a crop of high economic value, with 2 of 20 samples above the level, which is exactly the 10% accepted. The decision is close, so `voi` already gives the field priority. A high `c_needless` raises it further, and sends extra samples to settle whether the true share is below 10%.

The costs set where to sample, not what to decide. The decision stays with the decision rule. Raising the accepted share for valuable crops would trade health protection for money, which is a policy choice for the authorities.

### Costs from MCDM

MCDM turns the criteria of each unit into its two costs. The trade-off between the two kinds of error stays outside MCDM, as one setting for decision makers. Nothing here is decided.

Each cost has its own criteria:

- `c_needless` (restricting a unit that did not need it): economic value of the crop, dependence of local food security on it, number of farms and jobs, market reputation of the region.
- `c_missed` (releasing a unit that should have been restricted): population eating the produce, share eaten by the households that grow it, consumption rates, children, transfer of contamination from soil to crop.

Two MCDM runs give each unit a score between 0 and 1 for each cost. The existing machinery does this without change: callbacks compute the criteria per unit, `Optimizer` normalises and weights them, and the `CP` or `TOPSIS` score is the result. Most of these criteria are rasters (population, crop value, land use). `PriorCB` reads the mean of any raster over a unit, these included.

Normalised scores are relative to the other units. A score of 0.8 for economic value cannot be compared with a score of 0.8 for health risk. The ratio between the two costs is a policy choice, made explicit as one setting `r`:

    expected cost = c_needless * P(needless restriction) + r * c_missed * P(missed restriction)

MCDM sets the stakes among units for each kind of error. `r` sets the trade-off between the two kinds of error. Decision makers see and set `r` directly, next to the permissible level and the accepted proportion, instead of leaving it implicit in criteria weights.

MCDM also gives:

- A record of why each unit gets its samples: its decision is close (information layer) and its stakes are high (value layer).
- Sensitivity analysis: vary the criteria weights and `r`, then compare allocations and expected wrong decisions. Units sampled under every reasonable weighting are safe choices. Units whose samples depend on the weights show where decision makers must agree.

Gaps in the current MCDM layer:

- `LINEAR1` gives the lowest unit a score of 0. Its cost would be 0 and `voi` would never sample it, however close its decision. Costs need a floor, such as `c = c_min + score`, or a normalisation that never gives 0.
- Scores depend on the set of units. Adding or removing a unit changes every cost. Normalising against fixed reference values, such as the economic value of a typical field, keeps costs stable across campaigns.
- Sampler dose and deadlines are not stakes. They belong to the budget and the timing (see "Dilemmas that need new parts in trufl"), not to MCDM.

### Health as a limit

The testbed ("Two costs per unit" in `nbs/_scoring_experiments.ipynb`) shows that costs used only to allocate samples weaken health protection where economic value is high. Under the dashboard's rule, more samples can only restrict a unit that is not restricted, and can only lift a restricted one. When a needless restriction is expensive, sampling a clean-looking unit raises its expected cost. `voi` then stops sampling it, and contamination there goes unfound. On ten synthetic plumes, with a needless restriction costing 5 in half the units, missed restrictions in that half rose from 0.3 to 1.8 per campaign for `voi` without a prior, and from 1.3 to 8.5 with the dispersion prior.

Proposed: health is a limit, not a cost. `voi` first samples every unit whose probability of a missed restriction is above a bound, such as 5%, until it falls below it or more samples cannot lower it. The costs then decide where the remaining samples go. Economic value can then add samples to valuable units but cannot take them away from the health check. The bound is a policy setting, like the permissible level, for decision makers and DSS4NAFA to set. Nothing here is decided.

First test ("Health as a limit" in the experiments notebook, same plumes and costs, `voi(max_missed=...)`): a bound of 5% brings missed restrictions in the valuable half down to 0.2 to 0.3, but takes the whole budget, so the costs no longer act. A bound of 20% with the dispersion prior gives 1.6 missed restrictions there (8.5 without a bound, 1.3 with equal costs) and fewer needless ones than with equal costs (0.30 against 0.53). Without a prior, a bound of 20% barely helps, because a clean unit needs about 8 samples to reach it. The bound sets the trade-off between health protection and room for economic costs.

### Dilemmas that fit the two-cost model

- Food security against contamination. Where a staple feeds subsistence farmers, a restriction can cause more harm to health, through hunger and poor diet, than the dose it prevents. This raises `c_needless` for staples in poor areas.
- Livelihoods and communities against precaution. At Fukushima, the harm from relocation and loss of farming was large compared with the dose avoided. This cost belongs in `c_needless`, beyond the market price of the crop.
- Self-consumption against market produce. Market produce passes later checks; food a household grows and eats itself does not. A missed restriction on home gardens has no second barrier, so `c_missed` is higher there.
- Stigma against evidence ("fuhyo higai", harm from rumours). Buyers avoided Fukushima produce even below the limits. A needless restriction damages a region's reputation for years after it is lifted, which raises `c_needless`.

### Dilemmas that need new parts in trufl

- Speed against certainty. Leafy vegetables and milk can't wait for more rounds; stored grain can. trufl runs rounds with no clock. This needs a deadline, or a cost of delay, per unit.
- Sampler dose against information. Sampling near the plant exposes the teams, so a sample there costs more in dose as well as money. This needs a cost per sample that varies by unit, so the budget is no longer a count of samples.
- Coverage and equity against efficiency. `voi` sends samples where decisions are close, so settled or small units get few. Communities that see no sampling lose trust, and smallholders may get less protection than valuable estates. A minimum number of samples per unit is partly a fairness and trust constraint, not only a statistical one.
- Restriction against countermeasures. Potassium fertiliser, deep ploughing, clean feed for livestock and a change of crop are options as well as restriction. With more than two actions, the decision rule chooses among options instead of comparing with a threshold.
- Which commodity to sample. Transfer from soil to crop differs a lot between crops, so one field can be safe for grain and unsafe for mushrooms. The unit becomes a pair of field and crop.

Proposed priority: speed (deadlines) and sampler dose (variable sample cost) first, since both occur in every response and both change where samples go. Equity and decisions with several actions are larger design changes, for after the core is stable.

### Schedules: spend early or late?

Every experiment so far uses six rounds of 150 samples. `Campaign` takes any list of budgets per round, so other schedules need no new code, but none was tested before the experiment below. The answer depends on what the score values. The expectations below were written before that experiment.

With the current score, the wrong decisions at the end of the campaign, smaller and more frequent rounds should always help an adaptive strategy, because each sample is placed with more information. In the limit, one sample at a time is best. This score gives no value to deciding early.

Spending early pays only when time has a cost. A missed restriction exposes consumers for as long as it is in force, and a needless one costs income for each month it lasts. A time-weighted score would add up the cost of the decisions in force after each round, weighted by how long each round lasts. This is the cost of delay that "Speed against certainty" asks for. Under it, spending early is expected to win, by how much depending on the data:

- No prior: an early pilot spread over all units finds the close units before targeting can pay, which argues for spending early.
- A good prior, such as an airborne survey: the prior already shows the close units, so targeting works from the first round and spending early matters less.
- A poor prior: spending early protects against trusting it.
- A truth that changes: Cs-134 decays (half-life about 2 years), weathering moves contamination, and crops have harvest and market dates. Late samples measure a different state, and some decisions have deadlines. This favours spending early, and needs ground truths that change between rounds, which the simulation does not have.

The binding constraint may be capacity rather than choice: laboratory throughput and the number of field teams can fix the samples per week. The question then becomes how fast to ramp up, not when to spend.

First experiment ("Schedules" in `nbs/_scoring_experiments.ipynb`): front-loaded (300, 200, 150, 100, 100, 50), flat (150 each) and back-loaded (50, 100, 100, 150, 200, 300) schedules of 900 samples, on the ten plumes, with equal allocation, `bayes`, `voi` and `voi` with the survey prior, 10 seeds, rounds of equal length and a truth that does not change. A unit with no sample yet counts as not restricted. Differences between fields:

- At the end of the campaign, the schedule hardly matters: front-loading changes wrong decisions by 0.25 or less, and back-loading adds at most about 0.5 (`bayes` 0.53 ± 0.30, `voi` 0.49 ± 0.32). The expectation above, that this score favours spending late, is not supported.
- With the decisions in force, averaged over rounds, front-loading lowers wrong decisions by 1.7 to 1.8 against the flat schedule without a prior (9 or 10 of 10 fields), and back-loading raises them by 3.5 to 3.9 (all fields).
- The survey prior halves the gain from front-loading (0.90 ± 0.12), as expected above.

What can be concluded:

- The gain of front-loading on the score in force follows largely by construction: more samples earlier decide more units earlier, and back-loading starts with 50 units unsampled. Any score that values early decisions favours early samples. This part checks the bookkeeping more than it teaches.
- The finding is that spending early costs nothing at the end. Holding budget back to learn first and then target the close units gains nothing on these plumes. So the schedule is not a statistical trade-off here: time costs, deadlines and capacity should set it, not sampling efficiency. In practice: sample broadly as early as possible, and do not keep budget back for later targeting.
- A good prior makes the schedule matter less, because it already shows where the close units are.

What could change this conclusion:

- A truth that changes. Japan lifts a restriction only with 3 or more samples per municipality from the last month. With decay and weathering, late samples are needed to lift restrictions, which is a reason to keep budget for later rounds that a static truth cannot show.
- The default for a unit with no sample. Here it counts as not restricted. Early restrictions in Fukushima were broad and precautionary; with that default, unsampled units count as needless restrictions instead. This would change the size of the effect, probably not its direction.
- Many small rounds, where adaptive targeting has the most room to help, are not tested.

The next informative experiment needs a truth that changes between rounds, with decisions to lift restrictions. Also not tested yet: deadlines and a capacity limit per round. Nothing here is decided.

### Dilemmas for the policy, not for trufl

- Strict against lenient levels. Japan's limit for general food is 100 Bq/kg; the Codex guideline level is 1000 Bq/kg. A strict level builds trust and helps trade, but leads to more restrictions. The authorities set the level, and trufl takes it as input.
- Fine against coarse restriction units. Restricting a whole municipality is simple but restricts clean land. Partial restrictions need more samples. trufl could show what each unit size costs in samples, but the choice stays with the authorities.

## Design-based and model-based inference

The two approaches differ in where the randomness comes from. Brus and de Gruijter (1997) set out the choice for soil surveys, after de Gruijter and ter Braak (1990).

- Design-based. The field's values are fixed and unknown. The randomness comes only from the choice of sample locations. Each location must have a known chance of selection above zero, as in simple random, stratified or systematic random sampling. Estimators such as Horvitz–Thompson weight each sample by the inverse of that chance. Bias and variance are taken over the samples the design could have drawn. The target is a quantity of the actual unit, such as its true share of cells above the level. The results need no assumption about spatial structure, but the samples must come from a probability design.
- Model-based. The field is one draw from a random process, such as a Gaussian random field with a trend and a variogram. Sample locations are fixed and can be chosen on purpose. Inference uses the model and is conditional on the samples, as in kriging or Bayesian geostatistics. The results are valid only if the model is adequate. Purposive or convenience locations are acceptable if, given the model's covariates, the choice of location does not depend on the value there. The model also predicts at places without samples: maps, sub-unit posteriors and clusters.

| | Design-based | Model-based |
|---|---|---|
| Source of randomness | Selection of locations | The process that made the field |
| Sampling requirement | Probability design with known chances | Any choice of locations that does not depend on the values |
| Validity rests on | The design | The model |
| Target | A quantity of the whole unit | Predictions at points and over areas, including parts of a unit |
| Efficient layouts | Stratified random | Spatial coverage, or layouts that minimise kriging variance |
| Strength | Large samples, few assumptions | Small samples, where spatial correlation adds information |

In trufl, the beta-binomial share model is a model, but it treats a unit's samples as random draws within the unit. Its validity is design-based in this sense. The spread placement strategies and the prior raster use model-based ideas. The two sections below depend on this distinction. Convenience data break the random-draw assumption (see "Data without a sampling plan"). Partial restriction needs estimates for parts of a unit, which only a model gives (see "Partial restriction").

## Partial restriction

The share rule pools all samples in a unit. With 10% accepted, a hot cluster that covers 5% of a unit passes the rule. Restricting part of a unit goes beyond the rule and needs its own cost. Without that cost, a method that is allowed to split units splits all of them.

A unit's samples alone rarely show a cluster. About 10 samples often miss a cluster that covers a small part of the unit. Most of the information about where a cluster lies comes from the prior raster, such as the airborne survey, and the samples confirm it.

Two ways to flag a unit that may need splitting:

- A spatial scan statistic on the unit's samples tests for a sub-area where the share above the level is at least 10%. It is cheap and easy to explain, and uses the samples only.
- A posterior map at a resolution finer than the unit combines the prior raster and the samples. The flag is the probability that some sub-area has a share of at least 10%.

Proposed decision: compare the expected cost of three actions for the unit: restrict all of it, restrict none of it, or restrict part of it. The cost of a partial restriction is the expected wrong decisions in each part plus a split cost for administration, enforcement and public trust. This is the expected-cost comparison of `voi` with one more action.

The candidate parts decide most of the method:

- Administrative or field boundaries, such as former villages or parcels. The method chooses which parts to restrict, and the result is simple to enforce. Japan is thought to have restricted rice by former municipality after 2011 (not yet checked against a source).
- One straight cut, such as a clean west and a hot east. The method searches the angle and the offset, starting from the direction of the prior's gradient or of the plume edge (see "Directional fields and plumes").
- Recursive cuts on coordinates, as in a decision tree. A rule such as "east of this road is restricted" is easy to explain. With few samples, the cuts overfit.

With partial restriction as an action, `voi` values a sample by how much it lowers the expected cost of the best action for its unit, split included. Samples then go to the likely cut line. On the synthetic plumes, that line is the plume edge, where the close decisions are.

Proposed first step: one straight cut, the three actions and a split cost, on the synthetic plumes where the edge crosses units, scored by wrong decisions weighted by area. Nothing here is decided.

## Data without a sampling plan

In an emergency, many institutions collect samples without a common sampling plan: near roads and villages, or at places with higher dose, as Japan's guidelines asked. These data cannot be discarded.

`voi` allocates only the planned samples, given all data so far, and works with any data. The information layer under it fails. The beta-binomial model per unit uses the share of samples above the level as an estimate of the share of the unit's area above the level. That estimate is unbiased only when samples are placed at random within the unit. Samples near roads or at hot spots bias it. The DSS4NAFA share rule has the same bias.

Model-based geostatistics does not need random locations (Diggle and Ribeiro, "Model-based Geostatistics", 2007; Brus and de Gruijter, Geoderma, 1997, on design-based and model-based inference). The method fits a spatial model of the field to all data at their coordinates, with the prior raster as a covariate, by regression kriging or a Bayesian Gaussian process. Each unit's posterior share above the level is then an integral over the unit. The inference is valid when the choice of locations does not depend on the values beyond what the covariates explain. This is the spatial form of "missing at random".

Sampling is preferential when samplers choose places because of their values, as with hot spots. Two remedies exist:

- Add the drivers of the choice as covariates: survey dose rate, distance to roads, the institution.
- Model the locations and the values together (Diggle, Menezes and Su, "Geostatistical inference under preferential sampling", 2010).

Institutions and laboratories differ in bias and in noise. A random effect per institution models both, and extends the measurement noise of #11.

A small planned sample, placed by `voi`, calibrates the bias of the convenience data. Survey statistics has methods that combine a probability sample with non-probability data, such as mass imputation and doubly robust estimators.

In trufl, `voi` stays and a spatial posterior replaces the beta-binomial per unit. Each round, the convenience data update the posterior, and `voi` places the planned budget given all data. `voi` could also tell the other institutions where their next samples help most. The same posterior gives the map finer than the unit that partial restriction needs.

The approach needs the coordinates of every sample, and ideally its institution and the reason it was taken.

Proposed test: add convenience samples to the simulation, near a road network or biased towards hot spots. Compare `voi` with the beta-binomial and with a spatial posterior, with and without a small planned sample. Nothing here is decided.

## Simulation module

Proposed module `trufl.simulation`, exported from `nbs/07_scoring.ipynb`:

- `Campaign(fname_raster, gdf_units, score)` with `reset(seed)` and `step(n)`, `run(campaign, strategy, budgets, seed)` and `compare(campaign, strategies, budgets, seeds, summary)`.
- `unit_values`, `degrade` (prior rasters), and the scores `decisions` and `unit_stats` with their summaries.
- The baselines `equal`, `neyman`, `bayes`, the oracles, `cumulative_min`, and `mcdm` for the how-to strategy.

Its main use is comparing strategies before an emergency, on simulated ground truths. Measurement noise in `DataCollector` (#11) belongs here too.

### Reinforcement learning as a benchmark

`voi` is greedy: each round, it gives samples where they help most now, looks at most `horizon` samples ahead per unit, and treats units as independent. A policy trained by reinforcement learning could plan the whole campaign. It could save budget for later rounds, stop sampling a unit that later rounds will settle more cheaply, and use links between units, such as neighbours in a plume. It could also handle effects that have no closed form: spatial correlation, adaptive placement within a unit, measurement noise, deadlines and sampler dose.

`Campaign` already has the interface of an environment (`reset`, `step`). The reward would be minus the cost of the wrong decisions at the end of the campaign, with the health bound as a constraint (constrained reinforcement learning).

The costs: training needs many simulated campaigns, so the policy is only as good as the synthetic ground truths are realistic. A learned policy is much harder to explain to decision makers than `voi`. A hard health bound is harder to guarantee than with `voi`'s explicit first pass.

Proposed: use reinforcement learning as a benchmark, not as the method. It would show how far any strategy can improve on `voi`, and in which situations. Where the gap is large, the insight goes into `voi` in an explainable form, such as an effective sample count or a rule for saving budget across rounds. Nothing here is decided.

## Changes to published behaviour

Each of these needs your decision:

1. `StdCB` returns NaN below 2 samples, and uses the sample standard deviation (`ddof=1`). Today a unit with one sample gets 0, which ranks it as the least uncertain.
2. `MoranICB`: return 0 when Moran's I is not significant, return I always with the p-value as a second variable, or keep NaN for both cases and document it. A significant negative Moran's I already stopped a run (`LINEAR1` rejects negative values).
3. `LINEAR1` rejects any zero or negative value. Options: make `LINEAR2` the default in examples and the how-to, or clip, or document. This matters less if information criteria leave the recommended path, since value criteria are rarely negative.
4. `rank_to_sample` stays as it is. The how-to page keeps working; a new how-to shows `voi`.
5. New public modules or functions: the rule class, `voi`, `expected_wrong`, `allocate`, and `trufl.simulation`. Names and module boundaries are open.

## Out of scope for the first version

- Stakes data and their elicitation. The value layer starts with weight 1 for every unit.
- The asymmetry between a missed and a needless restriction (see "Two costs per unit"), and the other dilemmas.
- Several foodstuffs and radionuclides sharing one budget.
- "Partially restrict". Placement within a unit stays uniform random in the first version (see "Placement within a unit" and "Partial restriction").
- How to set the weight of a prior from its quality.
- Reinforcement learning, except as a benchmark (see "Reinforcement learning as a benchmark").

## Questions for DSS4NAFA

- The sawtooth: with the current rule, one more sample can make a decision less reliable. With 10% accepted, a unit whose true share is 12% is decided wrongly 28% of the time with 10 samples and 61% with 11.
- Should restriction decisions use prior information, such as the airborne survey, as well as samples?
- Is the share of samples above the permissible level the right criterion, or should decisions target what it stands for, such as dose to consumers? See "Is the share rule the right criterion?".
- Would decision makers accept setting the ratio `r` between the cost of a missed and of a needless restriction openly, as a dashboard setting next to the permissible level and the accepted proportion? See "Costs from MCDM".
- What bound on the probability of a missed restriction per unit would be acceptable, and should it be the same for every unit? See "Health as a limit".
- Must a partial restriction follow administrative or field boundaries, or may it follow any line? What does "Partially restrict" mean in the dashboard? See "Partial restriction".
- Do the data that reach DSS4NAFA in an emergency record each sample's coordinates, its institution and the reason it was taken? See "Data without a sampling plan".
- Which constraint binds the sampling schedule in practice: deadlines such as harvest or market dates, how long consumers are exposed, or laboratory and field capacity? See "Schedules: spend early or late?".

## Proposed order

Each step fits one commit, after your decisions above:

1. The `StdCB` and `MoranICB` changes, if agreed.
2. The decision rule class, `expected_wrong` and `voi` in the library, with `voi` taking stake weights (all 1 by default).
3. `trufl.simulation`, exported from `nbs/07_scoring.ipynb`, with measurement noise.
4. A how-to that plans a round with `voi`, and an explanation page on the roles of the decision rule, the information layer and MCDM.
5. Turning MCDM scores into stake weights, once stakes data exist.
