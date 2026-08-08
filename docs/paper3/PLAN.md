# Paper 3: validation plan

> **Does an average brain predict any brain? Held-out validation of the released TRIBE v2
> average-subject checkpoint**

## The claim under test

A commercial lab has published a zero-shot audit reporting that the released checkpoint, in
the average-subject configuration Monarch runs, is anti-correlated with real cortex: vertex
`r = -0.0145` against a measured inter-subject ceiling of `+0.0508`. Four subjects, one
stimulus, magnitudes near 0.015 either way. It is a sign claim, not an effect-size claim, and
it has not been independently replicated.

## Correction to the feasibility stated in PAPERS.md

`docs/PAPERS.md` says the checkpoint "outputs fsaverage5, the same surface CNeuroMod and
Algonauts publish". The first half holds and the second does not.

- **The checkpoint** emits 20484 fsaverage5 vertices. Confirmed in `tribe-ckpt/config.yaml`
  (`mesh: fsaverage5`) and in the smoke test's `(T, 20484)`, which is 2 x 10242.
- **The Algonauts 2025 public release** is not a surface. It is fMRI normalised to MNI and
  reduced to 1000 Schaefer parcels, distributed as `.h5`, CC0, through CONP and the
  `courtois-neuromod/algonauts_2025.competitors` repository, obtainable with datalad.

So the two do not meet without a projection step. This changes the work, not its feasibility,
and it is still true that no large GPU is needed.

## Two comparisons, deliberately kept apart

**Parcel-level, runnable on CC0 data now.** Project the checkpoint's 20484 vertices into the
1000 Schaefer parcels with `app/services/parcellation.py`, then correlate against the public
responses. This is also the space TRIBE was scored in for the competition, which makes it the
fair space for asking whether the released checkpoint performs as advertised.

**Vertex-level, a strict replication, needs more access.** Reproducing the audit's number in
its own units requires CNeuroMod surface derivatives rather than the parcellated competition
release, which means a data access request.

These must not be merged into one number. Averaging vertices within a parcel cancels
independent noise, so parcel r is systematically higher than vertex r on identical data. A
parcel-level result that looks better than `-0.0145` would not refute the audit; it would
only show that pooling raises correlations, which is arithmetic rather than a finding.
`test_parcellation.py` pins that effect with an explicit test so the claim is not rhetorical.

## Steps

1. Obtain the Algonauts 2025 competitors dataset via datalad. Record the exact commit.
2. Confirm subjects, sessions and the 1.49 s TR, and record which stimuli are held out.
3. Run the checkpoint over the same stimuli to produce `(T, 20484)` predictions.
4. Project predictions to 1000 parcels. Record vertices per parcel and any empty parcels.
5. Align on the time base. This is where errors hide: an off-by-one TR silently destroys the
   correlation and looks like a null result.
6. Compute per-parcel Pearson r with `app/services/encoder_validation.py`.
7. Compute the leave-one-subject-out noise ceiling from the same data, never assumed.
8. Bootstrap over subjects with a recorded seed.
9. Report sign and magnitude as measured, against the ceiling, with the spatial unit named in
   every figure caption and table header.

## Committed in advance

- The sign is the finding. Nothing is flipped or absolute-valued to improve a number.
- The ceiling is measured from the data in hand, not quoted from the audit.
- Four subjects is small. Report the interval, not just the point.
- If the parcel-level result disagrees with the audit, the first hypothesis is the spatial
  unit, not a refutation.
- Both outcomes are publishable, and both constrain every study built on this checkpoint.

## Status

Built and tested: `encoder_validation.py` (per-vertex r, leave-one-subject-out ceiling,
seeded bootstrap) and `parcellation.py` (vertex to parcel projection). Not started: the data
acquisition in step 1.

## Sources

- Algonauts 2025 competitors data and code:
  https://github.com/courtois-neuromod/algonauts_2025.competitors
- CONP portal record: https://portal.conp.ca/dataset?id=projects%2Falgonauts_2025_competitors
- TRIBE: https://arxiv.org/pdf/2507.22229
- Insights from the Algonauts 2025 winners: https://arxiv.org/pdf/2508.10784
