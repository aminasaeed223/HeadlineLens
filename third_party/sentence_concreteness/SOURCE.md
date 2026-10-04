Unmodified copy of `sentence_concreteness.py`, `concreteness_ratings.csv` and `LICENSE` (MIT) from
https://github.com/maubinle/sentence_concreteness

Aubin Le Quéré, M., Matias, J.N. When curiosity gaps backfire: effects of headline concreteness on
information selection decisions. Sci Rep 15, 994 (2025). https://doi.org/10.1038/s41598-024-81575-9

Vendored because `pip install sentence_concreteness` currently fails (setup.py lists the standard-library
modules `csv` and `string` as dependencies) and the module loads `concreteness_ratings.csv` from the
current working directory.
