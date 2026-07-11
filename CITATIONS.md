# Citations and third-party attribution

Monarch is a research / educational project (B.Sc Physics final-year work,
CUEA, and an AMD Developer Hackathon entry). It is **non-commercial**. The
components below carry their own licenses; the binding constraint is TRIBE v2's
CC-BY-NC-4.0, which permits research and hackathon use with attribution and
forbids commercial use.

## TRIBE v2 (Meta AI) - brain encoder, CC-BY-NC-4.0

Monarch's activation-prediction engine is Meta's TRIBE v2. Weights and code are
licensed CC-BY-NC-4.0 (non-commercial). Used here for research only.

```bibtex
@article{dAscoli2026TribeV2,
  title={A foundation model of vision, audition, and language for in-silico neuroscience},
  author={d'Ascoli, St{\'e}phane and Rapin, J{\'e}r{\'e}my and Benchetrit, Yohann and Brookes, Teon and Begany, Katelyn and Raugel, Jos{\'e}phine and Banville, Hubert and King, Jean-R{\'e}mi},
  year={2026}
}
```

## Frozen feature extractors

- **LLaMA 3.2-3B** (Meta) - text features. **Built with Llama.** Used under the
  Llama 3.2 Community License; gated on Hugging Face (accept terms, then
  authenticate with an HF read token). "Llama 3.2 is licensed under the Llama
  3.2 Community License, Copyright (c) Meta Platforms, Inc. All Rights Reserved."
- **Wav2Vec-BERT 2.0** (`facebook/w2v-bert-2.0`) - audio features. MIT.
- **V-JEPA 2 ViT-g** (`facebook/vjepa2-vitg-fpc64-256`) - video features. CC-BY-NC-4.0.
- **DINOv2-large** (`facebook/dinov2-large`) - image features (currently disabled).

## Physics / sociophysics

The Landau / Ising mean-field opinion-dynamics layer follows the statistical-
physics-of-social-dynamics literature; the social coupling constant default
(beta_j = 0.7) is taken from:

```bibtex
@article{Castellano2009,
  title={Statistical physics of social dynamics},
  author={Castellano, Claudio and Fortunato, Santo and Loreto, Vittorio},
  journal={Reviews of Modern Physics},
  volume={81}, number={2}, pages={591--646}, year={2009},
  publisher={American Physical Society}
}
```

## Language model for audit reports

Plain-language scan reports are generated with **Gemma** (Google DeepMind,
Apache-2.0) served via **Fireworks AI** on AMD hardware.
