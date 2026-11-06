# LinkedIn Projects entry

Paste into LinkedIn > Profile > Add profile section > Additional > Add project.

## Fields

| Field | Value |
|---|---|
| Project name | Monarch: Measuring the External Field |
| Associated with | The Catholic University of Eastern Africa |
| Currently working on this | No (tick only if you keep iterating after submission) |
| Start date | Set to when the project began |
| End date | Set to submission month |
| Project URL | https://monarch-4iy.pages.dev/corpus/ |
| Contributors | Add Dr. Songa Mutambi as supervisor if he is on LinkedIn |

LinkedIn allows one project URL only, so the visuals get the slot and the repository is named
in the description instead. Swap them if you would rather the link land on the code.
Repository: https://github.com/brn-mwai/monarch

Longer name if you prefer the full title: *Measuring the External Field: A Cortical-Proxy
Content Observable and the Mean-Field Bound on Media-Driven Opinion Change*

## Description

Undergraduate physics dissertation, supervised by Dr. Songa Mutambi.

The question: can media influence on opinion be written as an external field in a mean-field
model, and measured from content instead of assumed?

What I built:

1. An instrument. A released fMRI encoder predicts cortical response to a text item, and the
observable is the signed difference between two ROI unions, affective-salience and
deliberative-control. The ratio form the proposal specified proved undefined for 17.25%
of real content and was replaced by a signed difference, with the failure reported.

2. A corpus. 400 items across four framing categories, matched on length, every item scanned
and verified row by row.

3. The physics. A Landau expansion of the mean-field free energy gives a necessary condition
on any coupling capable of driving a population across the spinodal, alpha >= h_c(betaJ)/dX.
The measured spread dX = 0.1241 gives alpha >= 4.2938 at betaJ = 2.

What it found: the four categories separate at eta^2 = 0.1068 (F = 15.779, p = 1.0e-9)
against a design powered for 0.0268, and replicates in a second session (ICC = 0.8725). The effect is carried by fear-framed content. High-outrage content, expected to separate
most, does not separate on the index at all, but raises both component activations by nearly
the same amount, so its null is a symmetric response, not an absent one.

What it does not claim: each category is drawn from one source dataset, so category and
provenance are confounded and the separation cannot be attributed to framing. A TF-IDF
baseline reaches AUC 0.9758 against the index's 0.6274, so the index is a field observable, not a
manipulation detector. No participant was scanned, and the coupling is
unidentified: no fitted value appears anywhere.

Every item, its score and the figures: https://monarch-4iy.pages.dev/corpus/
Code: https://github.com/brn-mwai/monarch

Python, PyTorch, FastAPI, CUDA and ROCm, LaTeX. Three papers and a 78-page dissertation.

## Shorter description, if the long one crowds the profile

Undergraduate physics dissertation, supervised by Dr. Songa Mutambi. Asks whether the
influence of media on opinion can be written as an external field in a mean-field model and
measured from content rather than assumed.

I built the instrument, a content observable derived from a released fMRI encoder; the
corpus, 400 length-matched items across four framing categories; and the physics, a Landau
expansion giving a necessary condition on any coupling capable of driving a population across
the spinodal, alpha >= h_c(betaJ)/dX, which reaches alpha >= 4.2938 at betaJ = 2 on the
measured spread.

The four categories separate at eta^2 = 0.1068 against a design powered for 0.0268, and it
replicates across scanning sessions. It is also confounded: each category comes from one
source dataset, so the separation is between corpora and cannot be attributed to framing, and
a TF-IDF baseline classifies the same label better than the index does. Both are stated in
the abstract rather than the appendix.

Corpus and figures: https://monarch-4iy.pages.dev/corpus/
Code: https://github.com/brn-mwai/monarch

Python, PyTorch, FastAPI, CUDA and ROCm, LaTeX.
