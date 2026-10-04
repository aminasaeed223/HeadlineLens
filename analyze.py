"""
Does the headline concreteness measure travel to Pakistani English news?

Usage:
    python analyze.py --input "data/27k News Headlines 1 Jan 2020 - Mar 11 2021.csv"
    python analyze.py --input data/sample_headlines_SYNTHETIC.csv      # quick test only

Validation checks
  1. Coverage     How many headlines get dropped (more than 3 words with no rating), and which
                  words are missing from the rating list (local terms, British spellings, abbreviations)?
  2. Entities     Are Pakistani people, places and organizations recognized as entities (score 5)?
  3. Length       The measure was validated on 14-16 word headlines. How long are these headlines,
                  and how stable is the score for short ones?
  4. Determinism  Does the same headline always get the same score? (truecasing step)
  5. Localized    How much do scores change if missed Pakistani entities are counted as entities?
Findings (on scored headlines)
  6. Concreteness by section, by month, and for COVID vs other headlines.

Outputs: results/scored.csv, results/summary.json
"""

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from pkconc import analyze, sc

OUT = Path("results")
COVID_RE = re.compile(r"covid|corona|virus|lockdown|pandemic|\bsops?\b|vaccin|quarantin|ventilator|isolation",
                      re.IGNORECASE)
ABBREV = {"govt", "pm", "cm", "pc", "rs", "mna", "mpa", "sc", "hc", "ig", "dg", "ceo", "mou", "gb",
          "kp", "kpk", "sops", "sop", "bn", "mln", "pak", "intl", "dept", "vs", "covid-19", "t20", "odi", "nab"}
# British -> American spelling rewrites; a word counts as a British spelling only if the
# rewritten form exists in the rating list
UK_US = [("isation", "ization"), ("ising", "izing"), ("ised", "ized"), ("ises", "izes"), ("ise", "ize"),
         ("our", "or"), ("ours", "ors"), ("ogramme", "ogram"), ("tre", "ter"), ("ence", "ense"),
         ("yse", "yze"), ("lled", "led"), ("lling", "ling"), ("ae", "e"), ("oe", "e")]


def word_kind(w):
    if w in ABBREV:
        return "abbreviation"
    for uk, us in UK_US:
        if uk in w and sc.get_concreteness(w.replace(uk, us)) is not None:
            return "British spelling"
    return "local term, name or other"


def pick(cols, options):
    low = {c.lower(): c for c in cols}
    for o in options:
        if o in low:
            return low[o]
    for c in cols:
        if any(o in c.lower() for o in options):
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--limit", type=int, default=None, help="score only the first N headlines (for a quick run)")
    ap.add_argument("--threshold", type=int, default=3, help="unmatched words allowed (package default 3)")
    args = ap.parse_args()

    raw = pd.read_csv(args.input)
    hcol = pick(raw.columns, ["story heading", "headline", "heading", "title"])
    tcol = pick(raw.columns, ["timestamp", "date", "published"])
    scol = pick(raw.columns, ["section", "category"])
    df = pd.DataFrame({"headline": raw[hcol].astype(str).str.strip()})
    df["section"] = raw[scol].astype(str).str.strip() if scol else "All"
    df["date"] = pd.to_datetime(raw[tcol], errors="coerce") if tcol else pd.NaT
    df = df[df.headline.str.len() > 3].drop_duplicates("headline").reset_index(drop=True)
    if args.limit:
        df = df.head(args.limit)
    print(f"{len(df)} unique headlines | columns used: headline={hcol}, section={scol}, date={tcol}")

    t0, recs = time.time(), []
    for i, h in enumerate(df.headline):
        recs.append(analyze(h, args.threshold))
        if (i + 1) % 1000 == 0:
            print(f"  {i + 1}/{len(df)} scored ({time.time() - t0:.0f}s)")
    res = pd.concat([df, pd.DataFrame(recs)], axis=1)
    res["covid"] = res.headline.str.contains(COVID_RE)
    res["month"] = res.date.dt.to_period("M").astype(str)

    S = {"n_headlines": int(len(res)), "threshold": args.threshold, "source_file": Path(args.input).name}

    # 1. Coverage
    scored = res[res.status == "scored"]
    S["drop_rate"] = round(float((res.status != "scored").mean()), 4)
    S["drop_rate_local"] = round(float((res.status_local != "scored").mean()), 4)
    S["drop_reasons"] = res.status.value_counts().to_dict()
    unm = Counter(w for ws in res.unmatched for w in ws)
    S["n_unmatched_word_types"] = len(unm)
    S["top_unmatched"] = [[w, c, word_kind(w)] for w, c in unm.most_common(60)]
    kinds = Counter()
    for w, c in unm.items():
        kinds[word_kind(w)] += c
    S["unmatched_by_kind"] = dict(kinds)
    S["share_headlines_with_unmatched"] = round(float((res.unmatched.str.len() > 0).mean()), 4)

    # 2. Entities
    has_gaz = res.gazetteer_found.str.len() > 0
    S["share_with_pk_entity"] = round(float(has_gaz.mean()), 4)
    S["share_pk_entity_missed"] = round(float((res.loc[has_gaz, "gazetteer_missed"].str.len() > 0).mean()), 4) if has_gaz.any() else None
    found = Counter(n for ns in res.gazetteer_found for n in ns)
    missed = Counter(n for ns in res.gazetteer_missed for n in ns)
    S["entity_miss_table"] = sorted([[n, found[n], missed.get(n, 0), round(missed.get(n, 0) / found[n], 3)]
                                     for n in found if found[n] >= 3], key=lambda r: -r[1])[:40]
    S["top_spacy_entities"] = Counter(e.lower() for es in res.entities_spacy for e in es).most_common(40)

    # 3. Length
    res["len_bucket"] = pd.cut(res.n_words, [0, 6, 9, 13, 16, 100], labels=["1-6", "7-9", "10-13", "14-16", "17+"])
    S["length_mean"] = round(float(res.n_words.mean()), 2)
    S["share_in_validated_range"] = round(float(res.n_words.between(14, 16).mean()), 4)
    S["length_buckets"] = (res.groupby("len_bucket", observed=False)
                           .agg(n=("headline", "size"),
                                scored=("score", lambda s: float(s.notna().mean())),
                                mean=("score", "mean"), sd=("score", "std"))
                           .round(3).reset_index().astype({"len_bucket": str}).to_dict("records"))

    # 4. Determinism: re-score a sample and compare
    samp = res.sample(min(300, len(res)), random_state=0)
    again = [analyze(h, args.threshold)["score"] for h in samp.headline]
    diff = [not ((a is None and b is None) or (a is not None and b is not None and abs(a - b) < 1e-9))
            for a, b in zip(samp.score, again)]
    S["determinism"] = {"n_rescored": int(len(samp)), "n_changed": int(sum(diff))}

    # 5. Localized scores
    both = res[(res.status == "scored") & (res.status_local == "scored")]
    shift = both.score_local - both.score
    S["local_shift"] = {"mean": round(float(shift.mean()), 4), "share_changed": round(float((shift.abs() > 1e-9).mean()), 4),
                        "share_changed_over_0_25": round(float((shift.abs() > 0.25).mean()), 4),
                        "corr_original_local": round(float(both.score.corr(both.score_local)), 4) if len(both) > 2 else None}

    # 6. Findings
    S["overall_mean"] = round(float(scored.score.mean()), 3)
    S["by_section"] = (res.groupby("section")
                       .agg(n=("headline", "size"), drop_rate=("score", lambda s: float(s.isna().mean())),
                            mean=("score", "mean"), mean_local=("score_local", "mean"))
                       .round(3).sort_values("n", ascending=False).reset_index().to_dict("records"))
    S["by_month"] = (res.dropna(subset=["date"]).groupby("month")
                     .agg(n=("headline", "size"), mean=("score", "mean"), mean_local=("score_local", "mean"),
                          covid_share=("covid", "mean"))
                     .round(3).reset_index().to_dict("records"))
    S["covid_vs_other"] = {k: {"n": int(len(g)), "mean": round(float(g.score.mean()), 3),
                               "mean_local": round(float(g.score_local.mean()), 3),
                               "drop_rate": round(float(g.score.isna().mean()), 4)}
                           for k, g in [("covid", res[res.covid]), ("other", res[~res.covid])]}
    S["most_concrete"] = scored.nlargest(10, "score")[["headline", "score"]].round(2).values.tolist()
    S["least_concrete"] = scored.nsmallest(10, "score")[["headline", "score"]].round(2).values.tolist()

    OUT.mkdir(exist_ok=True)
    keep = ["headline", "section", "date", "n_words", "covid", "score", "status", "score_local", "status_local",
            "unmatched", "entities_spacy", "gazetteer_found", "gazetteer_missed"]
    out = res[keep].copy()
    for c in ["unmatched", "entities_spacy", "gazetteer_found", "gazetteer_missed"]:
        out[c] = out[c].map(lambda xs: "; ".join(xs))
    out.to_csv(OUT / "scored.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(S, indent=2, default=str), encoding="utf-8")
    print(f"done in {time.time() - t0:.0f}s")
    print(json.dumps({k: S[k] for k in ["drop_rate", "drop_rate_local", "share_with_pk_entity",
                                        "share_pk_entity_missed", "share_in_validated_range",
                                        "determinism", "local_shift", "overall_mean"]}, indent=1))


if __name__ == "__main__":
    main()
