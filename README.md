# Does headline concreteness travel?
### Testing a validated headline measure on Pakistani English news

Aubin Le Quéré & Matias (2025) built a **headline concreteness** measure and validated it on U.S. Upworthy
headlines of 14 to 16 words. The package README notes that other contexts may need additional validation.
This project does that for Pakistani English-language news: it runs the measure **unchanged** on about 27,000
Pakistani headlines and checks where it holds up and where it needs local adjustment.

> Paper: Aubin Le Quéré, M., Matias, J.N. *When curiosity gaps backfire: effects of headline concreteness on
> information selection decisions.* Sci Rep 15, 994 (2025). https://doi.org/10.1038/s41598-024-81575-9
> Package: https://github.com/maubinle/sentence_concreteness (MIT)

## The five checks

| Check | Question |
|---|---|
| Coverage | How many headlines are dropped (more than 3 unrated words)? Which words are missing: local terms, British spellings, abbreviations? |
| Entities | Are Pakistani people, places and parties recognized as entities (which the method scores 5)? |
| Length | What share of headlines falls inside the validated 14 to 16 word range, and how stable are scores for short ones? |
| Determinism | Does the same headline always get the same score? |
| Localized variant | How much do scores change when missed Pakistani entities are counted as entities? |

Then: concreteness by newspaper section, by month, and COVID headlines vs the rest.

`pkconc.analyze()` traces the method step by step using the package's own functions. It was checked to give
**identical scores** to `get_sentence_concreteness()` on every test headline.

## Run it

```bash
pip install -r requirements.txt

# 1. Get the data (free): "Pakistan News Headlines" on Kaggle, or
#    https://opendata.com.pk/dataset/pakistan-news-headlines  ->  put the CSV in data/
# 2. Score and analyze (a few minutes for ~27k headlines; use --limit 2000 for a quick run)
python analyze.py --input "data/27k News Headlines 1 Jan 2020 - Mar 11 2021.csv"
# 3. Explore
streamlit run app.py
```

`results/` currently holds output from `data/sample_headlines_SYNTHETIC.csv`: 55 example headlines written to
test the code. **They are not findings.** The app shows a banner until you run `analyze.py` on the real file.

## Files

| File | Purpose |
|---|---|
| `third_party/sentence_concreteness/` | The original package, unmodified (see SOURCE.md) |
| `pkconc.py` | Step-by-step trace of the method, plus the localized variant |
| `gazetteer.py` | Editable list of ~150 Pakistani people, places and organizations |
| `analyze.py` | Runs all checks and findings, writes `results/` |
| `app.py` | Streamlit app: score any headline live, view checks and findings |

## Early observations from the test headlines (confirm on real data)

- **British spellings** such as *programme*, *criticises*, *litre* are not in the U.S. rating list.
- **Local abbreviations and terms** (*govt*, *PSL*, *PDM*, *tehsil*) are unrated.
- **Partial names:** in "PM Imran Khan chairs...", spaCy tags only *Khan*; *Imran* counts as an unrated word.
- **False entities:** *coronavirus*, *SOPs* and *tehsil* were tagged as entities and scored the maximum 5.
- **Word sense:** *till* (as in "till end of month", meaning *until*) gets 4.0 because the rating list
  means a cash till.

## Limitations

The entity list is hand-built and incomplete. The localized variant only fixes entities; it does not invent
ratings for local words, which would break the validated scale. This project tests the *measure*, not whether
concreteness changes what Pakistani readers click.

## Note on installation

`pip install sentence_concreteness` currently fails because `setup.py` lists the standard-library modules
`csv` and `string` as dependencies, and the module reads `concreteness_ratings.csv` from the working directory.
The package is therefore vendored unmodified, and `pkconc.py` loads it from its own folder.

Built by Amina Saeed.
