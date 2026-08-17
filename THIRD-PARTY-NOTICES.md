# Third-party notices

## RiskShard

`risk-benchmarks.json` is derived from [RiskShard](https://github.com/raviaxo/RiskShard) by
[raviaxo](https://github.com/raviaxo), licensed **AGPL-3.0**. The generating commit is recorded in
the `source.commit` field of the data file and shown in the footer of the explorer page.

What is carried across, and how:

| From RiskShard | Into this repo |
|---|---|
| `risk_modules/*.yaml` | shard identity, country, industry, threat, tags |
| `scenarios/*.yaml` | the frequency and impact three-point estimates, currency, maturity labels |
| `calibrations/*.yaml` | the per-parameter `rationale` and transform |
| `evidence/*.yaml` | per-parameter source name, URL, publication date, confidence, `limitations` |
| `risk_modules/*.yaml` → `practitioner_notes` | the `not_good_for` and `good_for` statements |

The numbers are reproduced unchanged. The accompanying prose — parameter limitations, calibration
rationales, and the "not good for" statements — is RiskShard's own wording, carried verbatim
rather than paraphrased, because paraphrasing a caveat is how caveats get weakened. This project
is AGPL-3.0-or-later, the same licence as the upstream, so that redistribution is permitted; the
flattening, the JSON schema, the build script, and the explorer page are this project's own work.

Nothing here is endorsed by RiskShard, and this repo is not a RiskShard release. For the governed
originals, the calibration workflow, and the maturity programme, go upstream.

## The underlying sources

The shards cite 37 distinct public sources across 31 publisher domains — national statistics
offices, regulators, law-enforcement reporting, insurance-claims studies, and vendor surveys.
Examples include the UK Cyber Security Breaches Survey (DSIT), FBI IC3, the Australian Bureau of
Statistics, ACCC Scamwatch, Statistics Canada, CNIL, Japan's National Police Agency, the Singapore
Police Force, NetDiligence, Sophos, IBM, and Verizon.

**None of those publications are reproduced here.** What this repo carries is a citation — the
publisher's name, a URL, a publication date, and a short factual statement of the figure taken and
what limits its use. Extracted figures and bibliographic details are facts about the sources, not
copies of them. Each source remains the property of its publisher and is subject to that
publisher's own terms; follow the URL and read the original before relying on any number.

If you are a publisher named here and want a citation corrected or removed, open an issue.
