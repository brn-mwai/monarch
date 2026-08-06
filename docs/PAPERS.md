# Two journal articles, and the physics in each

Dr. Mutambi's standing requirement from the proposal defence: two published journal
articles in addition to the project document. This maps both, states where the physics
sits in each, and dates the work.

The rule applied throughout: **the neural encoder is the thermometer, not the physics.**
The physics is the statistical mechanics of a coupled population under an external field,
and what a measured field value implies for it. A paper that is mostly about the encoder
is not a physics paper and does not count against this requirement.

---

## Paper 1: bounding the external field in mean-field opinion dynamics

**Independent of the scan.** Every result is analytic or computed on a CPU, so this can be
drafted while the GPU run is still queued.

### The gap it addresses

Social Ising studies carry an external field `h` that is assigned by hand: a coupling
strength, a propaganda term, a media bias parameter. It is chosen to make figures, never
measured, and its magnitude is almost never justified. The consequence is that the
literature can show a population tipping without establishing that any real influence is
strong enough to tip it.

### The physics, section by section

1. **Model.** Ising Hamiltonian on a fully connected graph,
   `H = -J Σ⟨i,j⟩ sᵢsⱼ - h Σᵢ sᵢ`, with the mean-field self-consistency
   `m = tanh(βJ m + βh)`.

2. **Landau expansion.** `artanh(m) ≈ m + m³/3` gives
   `F(m) = a m² + b m⁴ - h m` with `a = (1 - βJ)/2` and `b = 1/12`. These coefficients
   are derived rather than asserted; the form widely quoted in this corner of the
   literature does not follow from its own self-consistency condition, and the
   discrepancy is worth one paragraph.

3. **Phase structure.** Second-order transition at `βJ = 1` in zero field. For `h ≠ 0`
   the transition becomes a crossover, with a bistable region bounded by the spinodal.
   The critical field `h_c(βJ)` is the boundary above which a single well survives.

4. **Numerical verification.** The solver recovers the mean-field exponents
   `β = 1/2`, `γ = 1`, `δ = 3`. This validates the implementation against exact results
   before any of it is applied to data.

5. **The bound, which is the contribution.** For any proposed observable `X` used as a
   field, `h = α X`, the population cannot be driven across the boundary unless

   ```
   α  ≥  h_c(βJ) / ΔX
   ```

   where `ΔX` is the spread of the observable across real content. This inverts the usual
   question. Instead of fitting `α` and hoping it is non-zero, it states what `α` would
   have to be for the mechanism to work at all, and it applies to **any** candidate field
   observable, not only to this project's index.

6. **Consequence.** A screening criterion: any sociophysics paper proposing a media-driven
   transition can be checked against this bound before its data is collected.

**Venue.** Physica A, European Physical Journal B, or Journal of Physics: Complexity.
arXiv preprint under physics.soc-ph on submission day.

**Status of the inputs.** `landau.py` and `phase_map.py` are implemented and tested.
Missing: the exponent verification, the phase-diagram figure, and the `α_required` curve.

---

## Paper 2: an empirically anchored field from predictive neural encoding

**Waits on the scan.** This is the thesis compressed, with the physics kept in front.

### The physics, section by section

1. **The field mapping.** `h = α · NAA`, taking the observable from predicted cortical
   activity rather than from a chosen constant. This is the step the literature skips.

2. **Free-energy landscape at measured values.** `F(m)` evaluated at each content
   category's measured mean, showing how the landscape would deform across a range of `α`.
   The range is swept, never fitted, because the calibration is null.

3. **Susceptibility.** `χ(NAA)` across the same range: how sharply a population's opinion
   responds to a change in media diet, and where that response is largest.

4. **The constraint, joined to Paper 1.** The measured spread `ΔNAA` over 400 items goes
   into `α ≥ h_c(βJ)/ΔNAA`, turning a null calibration into a quantitative statement about
   how strong the content-to-opinion coupling would have to be. **A null result becomes a
   bound**, which is a physics result rather than an absence of one.

5. **The measurement chapter, kept honest.** Instrument, corpus design, length matching,
   source balancing, removal of publisher tells, the cortical-proxy limitation, the null
   with its power statement, AUC as the headline. The apparatus is described here as
   methods; it is not the subject of the paper.

**Venue.** Physica A or Entropy.

---

## What is not a separate paper

The finding that the released TRIBE v2 checkpoint predicts only cortical surface vertices
is novel and unpublished, but it is a neuroscience-tooling result with no physics in it.
It belongs in Paper 2's methods, stated plainly, where it constrains the measurement. It
does not carry a physics paper on its own.

Likewise the software. A software-venue article (JOSS, SoftwareX) would be accepted and
would contain no physics, so it does not satisfy this requirement. The apparatus is
released alongside the papers as the reproducibility artifact.

---

## Dates

Proposed, subject to Dr. Mutambi's approval.

| Date | Item |
|---|---|
| 2026-08-07 | Amendment sent for sign-off; corpus scan starts |
| 2026-08-09 | Scan returns; analysis and corpus report run |
| 2026-08-13 | Project document submitted |
| 2026-08-27 | Paper 1 drafted (independent of the scan) |
| 2026-09-10 | Paper 1 submitted; preprint posted |
| 2026-09-24 | Paper 2 drafted |
| 2026-10-08 | Paper 2 submitted; preprint posted |

Paper 1 leads because it does not depend on the empirical result, which means one
submission is safe regardless of what the scan returns.
