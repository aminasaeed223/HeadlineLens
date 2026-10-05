"""
HeadlineLens: measuring headline concreteness in Pakistani English news.
Run:  streamlit run app.py
"""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from pkconc import analyze, sc

RESULTS = Path("results")
INK, ABSTRACT, CONCRETE, NONE, ENTITY = "#1D2433", "#5B6C9A", "#C58B1C", "#A0A7B2", "#8A3B2E"

EXAMPLES = [
    "PDM announces next power show in Multan",
    "Sindh govt extends lockdown till end of month",
    "SBP keeps policy rate unchanged at 7pc",
    "Tehsil hospital in Bahawalnagar receives new ventilators",
    "PM Imran Khan chairs NCOC meeting on rising coronavirus cases",
    "Ehsaas cash programme reaches 12 million families",
    "This simple idea could change how you think about happiness",
]

st.set_page_config(page_title="HeadlineLens", page_icon="🔎", layout="wide")
st.markdown(f"""
<style>
.block-container {{ padding-top: 3.2rem; }}
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Serif:ital,wght@0,500;0,600;1,500&display=swap');
html, body, [class*="css"], .stMarkdown {{ font-family: 'IBM Plex Sans', system-ui, sans-serif; }}
h1, h2, h3 {{ font-family: 'IBM Plex Serif', Georgia, serif; color: {INK}; font-weight: 600; }}
.headline {{ font-family: 'IBM Plex Serif', Georgia, serif; font-size: 1.35rem; line-height: 1.35; color: {INK};
             border-top: 3px solid {INK}; border-bottom: 1px solid {INK}; padding: .7rem 0; margin: .4rem 0 1rem; }}
.score {{ font-size: 2.1rem; font-weight: 600; color: {INK}; line-height: 1; }}
.label {{ color: #5E6672; font-size: .92rem; }}
.chip {{ display: inline-block; padding: 2px 9px; margin: 3px 4px 3px 0; border-radius: 3px; font-size: .95rem; }}
.note {{ color: #5E6672; font-size: .92rem; }}
.warn {{ background: #FFF4DC; border-left: 4px solid {CONCRETE}; padding: .6rem .9rem; margin-bottom: 1rem; }}
</style>""", unsafe_allow_html=True)


def chip(text, color, filled=True):
    style = f"background:{color}; color:white;" if filled else f"border:1px dashed {color}; color:{color};"
    return f'<span class="chip" style="{style}">{text}</span>'


def fmt(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and pd.isna(x)) else f"{x:.{d}f}"


def pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


@st.cache_data
def load_results():
    if not (RESULTS / "summary.json").exists():
        return None, None
    S = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    df = pd.read_csv(RESULTS / "scored.csv") if (RESULTS / "scored.csv").exists() else None
    return S, df


LOGO = f"""<svg width="58" height="58" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-label="HeadlineLens logo">
  <rect x="4" y="8" width="38" height="46" rx="3" fill="#FFFFFF" stroke="{INK}" stroke-width="3"/>
  <rect x="10" y="15" width="26" height="5" fill="{INK}"/>
  <rect x="10" y="25" width="26" height="2.5" fill="#A0A7B2"/>
  <rect x="10" y="31" width="20" height="2.5" fill="#A0A7B2"/>
  <rect x="10" y="37" width="14" height="2.5" fill="#A0A7B2"/>
  <circle cx="40" cy="38" r="13" fill="{CONCRETE}" fill-opacity="0.18" stroke="{CONCRETE}" stroke-width="4"/>
  <line x1="49.5" y1="47.5" x2="59" y2="57" stroke="{CONCRETE}" stroke-width="6" stroke-linecap="round"/>
</svg>"""

st.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; margin:0 0 .3rem">
  {LOGO.replace('width="58" height="58"', 'width="44" height="44"')}
  <div>
    <div style="font-family:'IBM Plex Serif',Georgia,serif; font-size:1.8rem; font-weight:600; color:{INK}; line-height:1.05">
      Headline<span style="color:{CONCRETE}">Lens</span></div>
    <div style="color:#5E6672; font-size:.85rem; letter-spacing:.05em; text-transform:uppercase">Measuring headline concreteness</div>
  </div>
</div>""", unsafe_allow_html=True)

tab_try, tab_valid, tab_find, tab_about = st.tabs(
    ["Score a headline", "Does the measure travel?", "Pakistani headlines", "About"])

# ------------------------------------------------------------------ try
with tab_try:
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        if "headline" not in st.session_state:
            st.session_state.headline = EXAMPLES[0]
        pick = st.pills("Try an example", EXAMPLES[:4], selection_mode="single", label_visibility="collapsed")
        if pick and pick != st.session_state.get("_last_pick"):
            st.session_state.headline = pick
            st.session_state._last_pick = pick
        headline = st.text_input("Headline", key="headline", placeholder="Type any English news headline",
                                 label_visibility="collapsed")

        if headline.strip():
            a = analyze(headline)
            st.markdown(f'<div class="headline">{headline}</div>', unsafe_allow_html=True)
            k1, k2 = st.columns(2)
            k1.markdown(f'<div class="label">Original method</div><div class="score">{fmt(a["score"])}</div>',
                        unsafe_allow_html=True)
            k2.markdown(f'<div class="label">With Pakistani names added</div><div class="score">{fmt(a["score_local"])}</div>',
                        unsafe_allow_html=True)
            if a["status"] != "scored":
                st.caption(f"Original method: {a['status']}")

            rows = [{"word": w, "value": v, "how": "rated word"} for w, v in a["matched"]]
            rows += [{"word": e.lower(), "value": 5.0, "how": "entity found by spaCy (scored 5)"} for e in a["entities_spacy"]
                     if not (len(e.split()) == 1 and sc.get_concreteness(e.lower()) is not None)]
            rows += [{"word": m, "value": 5.0, "how": "Pakistani entity spaCy missed"} for m in a["gazetteer_missed"]]
            chips = "".join(chip(f'{r["word"]} {r["value"]:.1f}', CONCRETE if r["value"] >= 3 else ABSTRACT)
                            for r in rows if r["how"] == "rated word")
            chips += "".join(chip(f'{r["word"]} 5', ENTITY) for r in rows if r["how"].startswith("entity"))
            chips += "".join(chip(f'{w} ?', NONE, filled=False) for w in a["unmatched"])
            chips += "".join(chip(f'{m}: missed name', ENTITY, filled=False) for m in a["gazetteer_missed"])
            st.markdown(f'<div style="margin-top:.8rem">{chips or "<span class=note>No content words found.</span>"}</div>',
                        unsafe_allow_html=True)

            with st.expander("How to read this"):
                st.markdown(f'<div class="note">'
                            f'{chip("rated", CONCRETE)} concrete-leaning &nbsp; {chip("rated", ABSTRACT)} abstract-leaning &nbsp; '
                            f'{chip("name", ENTITY)} named entity, counted as 5 &nbsp; {chip("?", NONE, False)} not in the rating list &nbsp; '
                            f'{chip("missed", ENTITY, False)} Pakistani name not caught<br><br>'
                            f'Scale 1 (abstract) to 5 (concrete). A headline is dropped when more than 3 of its words have no rating.</div>',
                            unsafe_allow_html=True)
                if rows:
                    plot = pd.DataFrame(rows)
                    base = alt.Chart(plot).encode(
                        x=alt.X("value:Q", scale=alt.Scale(domain=[1, 5]), title="Concreteness rating"),
                        y=alt.Y("how:N", title=None, axis=alt.Axis(labelLimit=240)),
                        tooltip=["word", "value", "how"])
                    rated = base.transform_filter(alt.datum.how == "rated word").mark_circle(size=180, opacity=1).encode(
                        color=alt.condition(alt.datum.value >= 3, alt.value(CONCRETE), alt.value(ABSTRACT)))
                    ents = base.transform_filter(alt.datum.how != "rated word").mark_circle(size=180, opacity=1, color=ENTITY)
                    text = base.mark_text(dy=-13, fontSize=11, color=INK).encode(text="word:N")
                    st.altair_chart((rated + ents + text).properties(height=70 + 40 * plot.how.nunique()), width="stretch")

# ------------------------------------------------------------------ validation
S, D = load_results()
NO_RESULTS = ("No results yet. Download the Pakistan News Headlines CSV into `data/`, then run "
              "`python analyze.py --input data/<file>.csv`.")


def synthetic_banner():
    if S and "SYNTHETIC" in S.get("source_file", ""):
        st.markdown('<div class="warn"><b>Test data.</b> These numbers come from 55 synthetic example headlines '
                    'used to check the code. Run <code>analyze.py</code> on the real dataset before quoting any result.</div>',
                    unsafe_allow_html=True)


with tab_valid:
    if not S:
        st.info(NO_RESULTS)
    else:
        synthetic_banner()
        st.markdown(f"**{S['n_headlines']:,} unique headlines** from `{S['source_file']}`, scored with the "
                    f"package defaults (up to {S['threshold']} unmatched words allowed).")

        st.subheader("1. Coverage: are the words in the rating list?")
        m1, m2, m3 = st.columns(3)
        m1.metric("Headlines dropped (original)", pct(S["drop_rate"]))
        m2.metric("Dropped after adding Pakistani entities", pct(S["drop_rate_local"]))
        m3.metric("Headlines with at least one unrated word", pct(S["share_headlines_with_unmatched"]))
        kinds = pd.DataFrame(list(S["unmatched_by_kind"].items()), columns=["Kind", "Occurrences"])
        st.altair_chart(alt.Chart(kinds).mark_bar(color=ABSTRACT).encode(
            x="Occurrences:Q", y=alt.Y("Kind:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260))).properties(height=120), width="stretch")
        st.dataframe(pd.DataFrame(S["top_unmatched"][:30], columns=["Unrated word", "Count", "Kind"]),
                     hide_index=True, width="stretch", height=300)
        st.markdown('<div class="note">The ratings (Brysbaert, Warriner & Kuperman, 2013) come from U.S. raters. '
                    'Pakistani English uses British spellings (programme, criticises), local abbreviations '
                    '(govt, pc, Rs) and local terms (tehsil, load-shedding) that are not in the list. Dropped '
                    'headlines are not random, which can bias averages.</div>', unsafe_allow_html=True)

        st.subheader("2. Entities: are Pakistani names recognized?")
        e1, e2 = st.columns(2)
        e1.metric("Headlines naming a listed Pakistani entity", pct(S["share_with_pk_entity"]))
        e2.metric("...where the entity step missed at least one", pct(S["share_pk_entity_missed"]))
        if S["entity_miss_table"]:
            st.dataframe(pd.DataFrame(S["entity_miss_table"], columns=["Entity", "Headlines", "Missed", "Miss rate"]),
                         hide_index=True, width="stretch", height=300)
        st.markdown("Entities found by spaCy most often (check for words that are not really names, "
                    "which get the maximum score of 5):")
        st.dataframe(pd.DataFrame(S["top_spacy_entities"][:25], columns=["Detected entity", "Count"]),
                     hide_index=True, width="stretch", height=260)

        st.subheader("3. Length: inside the validated range?")
        st.metric("Headlines with 14 to 16 words (the validated range)", pct(S["share_in_validated_range"]))
        lb = pd.DataFrame(S["length_buckets"]).rename(columns={"len_bucket": "Words", "n": "Headlines",
                                                                "scored": "Share scored", "mean": "Mean score", "sd": "SD"})
        st.dataframe(lb, hide_index=True, width="stretch")
        st.markdown('<div class="note">Short headlines average over fewer words, so one word moves the score '
                    'more. Compare the SD across length groups.</div>', unsafe_allow_html=True)

        st.subheader("4. Determinism and 5. local adjustment")
        d = S["determinism"]
        ls = S["local_shift"]
        st.markdown(f"""
- Re-scoring {d['n_rescored']} random headlines changed **{d['n_changed']}** scores (the package notes that its
  truecasing step is occasionally non-deterministic).
- Counting missed Pakistani entities as entities changes **{pct(ls['share_changed'])}** of scores
  ({pct(ls['share_changed_over_0_25'])} by more than 0.25 points). Mean change {ls['mean']:+.3f};
  correlation between original and adjusted scores **{fmt(ls['corr_original_local'], 3)}**.""")

# ------------------------------------------------------------------ findings
with tab_find:
    if not S:
        st.info(NO_RESULTS)
    else:
        synthetic_banner()
        st.markdown(f"Mean concreteness of scored headlines: **{S['overall_mean']:.2f}** on the 1 to 5 scale.")
        sec = pd.DataFrame(S["by_section"])
        sec = sec[sec.n >= max(5, int(0.005 * S["n_headlines"]))]
        long = sec.melt(id_vars=["section", "n"], value_vars=["mean", "mean_local"], var_name="version", value_name="score")
        long["version"] = long.version.map({"mean": "Original", "mean_local": "With Pakistani entities"})
        st.subheader("By section")
        st.altair_chart(alt.Chart(long).mark_bar().encode(
            y=alt.Y("section:N", sort="-x", title=None), x=alt.X("score:Q", scale=alt.Scale(domain=[1, 5]), title="Mean concreteness"),
            yOffset="version:N", color=alt.Color("version:N", scale=alt.Scale(range=[ABSTRACT, CONCRETE]), title=None),
            tooltip=["section", "n", "version", alt.Tooltip("score:Q", format=".2f")]
        ).properties(height=max(160, 46 * len(sec))), width="stretch")

        mon = pd.DataFrame(S["by_month"])
        if len(mon) > 1:
            st.subheader("Over time")
            base = alt.Chart(mon).encode(x=alt.X("month:N", title=None))
            line = base.mark_line(point=True, color=INK).encode(
                y=alt.Y("mean:Q", scale=alt.Scale(zero=False), title="Mean concreteness"))
            bars = base.mark_bar(opacity=.25, color=CONCRETE).encode(
                y=alt.Y("covid_share:Q", title="Share of COVID headlines", axis=alt.Axis(format="%")))
            st.altair_chart(alt.layer(bars, line).resolve_scale(y="independent").properties(height=280), width="stretch")

        cv = S["covid_vs_other"]
        st.subheader("COVID headlines vs everything else")
        st.dataframe(pd.DataFrame([{"Group": k, "Headlines": v["n"], "Mean (original)": v["mean"],
                                    "Mean (adjusted)": v["mean_local"], "Dropped": pct(v["drop_rate"])}
                                   for k, v in cv.items()]), hide_index=True, width="stretch")

        cA, cB = st.columns(2, gap="large")
        cA.markdown("**Most concrete**")
        cA.dataframe(pd.DataFrame(S["most_concrete"], columns=["Headline", "Score"]), hide_index=True, width="stretch")
        cB.markdown("**Least concrete**")
        cB.dataframe(pd.DataFrame(S["least_concrete"], columns=["Headline", "Score"]), hide_index=True, width="stretch")

        if D is not None:
            st.subheader("Browse all scored headlines")
            q = st.text_input("Filter by word")
            view = D[D.headline.str.contains(q, case=False, na=False)] if q else D
            st.dataframe(view[["headline", "section", "score", "score_local", "status", "unmatched", "gazetteer_missed"]].head(500),
                         hide_index=True, width="stretch", height=360)

# ------------------------------------------------------------------ about
with tab_about:
    st.markdown("""
### About
**Measure.** `sentence_concreteness` by Marianne Aubin Le Quéré (MIT license), used unchanged. It averages
word ratings from Brysbaert, Warriner & Kuperman (2013), gives named people, places and organizations the
maximum score of 5, and skips stopwords and numbers. Paper: Aubin Le Quéré, M. & Matias, J. N. (2025).
*When curiosity gaps backfire: effects of headline concreteness on information selection decisions.*
Scientific Reports 15, 994.

**What this project adds.** A step-by-step trace of the method for each headline (verified to give identical
scores to the package), and five checks for a new context: coverage, entity recognition, headline length,
determinism, and a localized variant that counts Pakistani entities from a small, editable list.

**Data.** Pakistan News Headlines: about 27,000 headlines from major Pakistani English-language newspapers,
January 2020 to March 2021 (Open Data Pakistan, ODbL; also shared on Kaggle).

**Limitations.** The entity list is hand-built and incomplete. The localized variant only fixes entities, not
missing ratings for local words, since inventing ratings would break the validated scale. Whether concreteness
affects clicks in Pakistan, as it did for Upworthy readers, is a separate question this project does not test.

Built by Amina Saeed.""")