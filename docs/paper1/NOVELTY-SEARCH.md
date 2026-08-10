# Paper 1 novelty search

Run 2026-08-10, before submission. Recorded so the novelty claim can be audited rather than
taken on trust, and so a referee question about prior art has a documented answer.

## The claim being tested

That no published work states a **necessary condition on the coupling** between a content
observable and the external field of a mean-field opinion model, in the form

    alpha >= h_c(beta_J) / dX

where `dX` is the observable's attainable range, evaluable **before** any data is collected
and usable to screen a proposed mechanism.

## Queries run

1. bound on coupling constant external field opinion dynamics mean-field Ising spinodal
   necessary condition
2. "content observable" / "media observable" calibrate external field sociophysics measured
   spread critical field threshold
3. necessary condition media-driven phase transition opinion model spinodal attainable range
   observable screening criterion 2025 2026
4. lower bound coupling strength external field opinion dynamics derived from observable
   range before data collection sociophysics falsifiable
5. Direct check of the closest prior work, arXiv:2510.00612

## Result

**Nothing found that states the bound or an equivalent.** The literature returned falls into
three groups, none of which pre-empts it.

**Field assigned and swept.** The dominant pattern. Mass media enters as a probability or a
field magnitude that is varied to see when the transition disappears: Crokidakis on the
Sznajd model, Azhari and Muslim on majority-rule and q-voter dynamics, the Axelrod
external-field literature. The swept parameter is exactly the quantity whose real-world
magnitude is at issue, and none of these bounds it.

**Field fitted from data.** Some work adjusts the field strength so that simulated agreement
fractions match survey data. This is calibration after the fact, the inverse of a screening
condition: it needs the outcome data first and produces a value rather than a requirement.

**Field measured, closest prior work.** Korbel, Dahdoul and Thurner calibrate a
double-random-field Ising model of elections against US House results 1980 to 2020 and
extract a critical campaign spending near 1.8 million USD. Their field is measured rather
than assigned, which is the same move this paper argues for, and Paper 1 says so explicitly
in its introduction. It remains distinct on two counts: their calibration is fitted from
outcome data after the fact and so cannot screen a proposal before the data exists, and it is
specific to expenditure rather than to a content observable.

## One correction this search produced

The Korbel reference was cited as an arXiv preprint. It has since appeared as **Phys. Rev.
Lett. 136 (2026) 127402**, and the citation is updated in `paper1.tex` and in the thesis
bibliography. Note that the arXiv landing page's own journal-ref string reads 2025, which is
inconsistent with PRL volume numbering and with the publisher listing from the authors'
institute; 2026 is used.

## Standing caveat

Absence of a result in five searches is weaker evidence than a systematic review. The claim
made in the paper is that the bound is not stated in the literature these searches cover, and
the paper positions itself against the closest prior work by name rather than claiming a
vacuum.
