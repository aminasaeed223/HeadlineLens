"""
Runs Marianne Aubin Le Quéré's sentence_concreteness method on a headline and records
what happened at each step, so we can see where it works and where it struggles on
Pakistani English news.

`analyze()` reproduces get_sentence_concreteness() step by step (same functions, same order,
same thresholds) and additionally returns:
  * which words were matched to a rating and which were not
  * which named entities spaCy found
  * which Pakistani entities from gazetteer.py were present but NOT found by spaCy
  * a "localized" score that treats those missed Pakistani entities as entities (score 5),
    exactly as the original method treats entities it does detect

The original package files in third_party/ are not modified.
"""

import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from string import punctuation

from gazetteer import GAZETTEER

PKG_DIR = Path(__file__).resolve().parent / "third_party" / "sentence_concreteness"


@contextmanager
def _cwd(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _ensure_nltk():
    import nltk
    for res, path in [("punkt", "tokenizers/punkt"), ("punkt_tab", "tokenizers/punkt_tab"),
                      ("stopwords", "corpora/stopwords"), ("wordnet", "corpora/wordnet"),
                      ("omw-1.4", "corpora/omw-1.4")]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(res, quiet=True)


_ensure_nltk()

with _cwd(PKG_DIR):                      # the module reads concreteness_ratings.csv from the cwd
    sys.path.insert(0, str(PKG_DIR))
    import sentence_concreteness as sc  # noqa: E402

# Gazetteer prepared for matching on lowercased, de-hyphenated text (as the method's NER step sees it)
_GAZ = sorted({(re.sub(r"[-\s]+", " ", name.lower()).strip(), etype) for name, etype in GAZETTEER},
              key=lambda x: -len(x[0]))
_GAZ_RE = [(re.compile(r"(?<![a-z])" + re.escape(n) + r"(?![a-z])"), n, t) for n, t in _GAZ]


def _find_gazetteer(text_nohyphen):
    """Longest-first, non-overlapping whole-word matches."""
    found, taken = [], []
    for rx, name, etype in _GAZ_RE:
        for m in rx.finditer(text_nohyphen):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            found.append((name, etype))
    return found


def _score(words, num_entities, threshold):
    unmatched = [w for w in words if sc.get_concreteness(w) is None and w not in punctuation]
    matched = [(w, sc.get_concreteness(w)) for w in words if sc.get_concreteness(w) is not None]
    values = [v for _, v in matched] + [5] * num_entities
    if len(unmatched) > threshold:
        status, score = "dropped: too many unmatched words", None
    elif not values:
        status, score = "dropped: no recognized words", None
    else:
        status, score = "scored", sum(values) / len(values)
    return score, status, matched, unmatched


def analyze(headline: str, threshold: int = 3) -> dict:
    sentence = str(headline).lower()
    nohyph = sentence.replace("-", " ")

    # --- original method, step by step
    entities, num_entities = sc.run_NER(nohyph)
    ent_tokens = [w for seg in entities for w in str(seg).lower().split()]
    words = sc.word_tokenize(sentence)
    words = sc.get_non_stopwords(words)
    words = [w for w in words if w not in ent_tokens]
    words = [w for w in words if not w.isnumeric()]
    score, status, matched, unmatched = _score(words, num_entities, threshold)

    # --- which Pakistani entities were present, and which did spaCy miss?
    gaz_found = _find_gazetteer(nohyph)
    ent_token_set = set(ent_tokens)
    missed = []
    for name, etype in gaz_found:
        toks = name.split()
        if all(t in ent_token_set for t in toks):
            continue                                   # spaCy found it
        if len(toks) == 1 and sc.get_concreteness(name) is not None:
            continue                                   # method rates single known words directly, as the original does
        missed.append((name, etype))

    # --- localized variant: treat missed Pakistani entities as entities (score 5)
    miss_tokens = {t for n, _ in missed for t in n.split()}
    miss_full = {n for n, _ in missed}

    def is_missed(w):
        parts = [p for p in re.split(r"[-\s]+", w) if p]
        return w in miss_full or (parts and all(p in miss_tokens for p in parts))

    words_local = [w for w in words if not is_missed(w)]
    score_l, status_l, _, unmatched_l = _score(words_local, num_entities + len(missed), threshold)

    return {
        "n_words": len(str(headline).split()),
        "score": score, "status": status,
        "matched": matched, "unmatched": unmatched,
        "entities_spacy": [str(e) for e in entities],
        "gazetteer_found": [n for n, _ in gaz_found],
        "gazetteer_missed": [n for n, _ in missed],
        "score_local": score_l, "status_local": status_l, "unmatched_local": unmatched_l,
    }


def original(headline: str, threshold: int = 3):
    """The unmodified package function, for checking that analyze() reproduces it."""
    return sc.get_sentence_concreteness(headline, num_unmatched_words_allowed=threshold)
