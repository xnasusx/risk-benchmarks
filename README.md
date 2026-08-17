# Risk Benchmarks

Source-backed starting ranges for cyber loss estimates, as one JSON file that browser tools can
load directly. Every number carries the source it came from, that source's stated limitation, and
what the shard will not support.

**Live:** https://rootcawsllc.github.io/risk-benchmarks/

![The Risk Benchmarks explorer. A header reports 12 shards, 8 countries, 72 parameters, 41 distinct sources and 4 currencies. Below, filters for country and threat sit above a grid of shard cards; each shows a frequency and loss three-point estimate in its own currency, badges for its maturity status, provenance tier and confidence mix, and a "not good for" caveat. The first card is expanded to show all six parameters, each naming its source, publication date, confidence level and the limitation on its use](preview.png)

Eleven shards, each one an annual event frequency and a per-event loss as three-point estimates,
ready to drop into a Monte Carlo. Expanding a shard shows where each of its six numbers came from
and why it should not be trusted further than it deserves.

## Why it exists

Interactive risk tools tend to ship with invented numbers. The ranges have to come from somewhere,
so the author makes them up, labels them "illustrative", and moves on. That is defensible for a
teaching tool and indefensible the moment anyone uses the output to make a decision.

The fix is not better invented numbers. It is numbers that arrive with their provenance attached,
so a range backed by six citations and a range typed from memory do not look equally
authoritative. This repo is that data, in a shape a single-file HTML tool can `fetch()`.

It exists as its own repo rather than being copied into each tool so there is one source of truth
and one place to regenerate when the upstream evidence changes.

## What it does

`risk-benchmarks.json` holds:

- **`benchmarks`** — 12 shards across 8 countries (AU, CA, DE, FR, GB, JP, SG, US) and four threats
  (business email compromise, data breach, ransomware, AI-enabled fraud), priced in AUD, CAD, GBP
  or USD. All 72 parameters resolve to a named public source. Each shard carries a
  **`provenance_tier`**:
  - **`module_governed`** (11) — upstream has a manifest tying the scenario to an org profile, a
    calibration record and its evidence, plus a practitioner statement of what it is not good for.
  - **`evidence_backed`** (1) — every parameter clears the same evidence bar, but there is no
    manifest: no calibration rationale, no practitioner review, and no stated `not_good_for`. The
    AI-enabled fraud shard sits here, and all six of its parameters are `low` confidence.

  **`confidence_summary`** counts parameters by confidence level, because a shard that is six-of-six
  `low` should not read like one that is six-of-six `medium`. None are `high`.
- **`examples`** — 9 scenarios with **no** provenance: demo fixtures and one loss-chain worked
  example. Kept in a separate array so a tool that reads `benchmarks` can never render an
  unsourced figure as if it were sourced.

Each benchmark:

```json
{
  "id": "gb_finance_data_breach_midmarket",
  "country": "GB", "industry": "financial_services", "threat": "data_breach",
  "currency": "GBP",
  "maturity": { "scenario_stage": "governed_starter",
                "benchmark_status": "starter_with_source_backed_uk_direct_parameters" },
  "frequency": { "min": 0.43, "likely": 0.65, "max": 0.69, "unit": "events_per_year" },
  "impact":    { "min": 10000, "likely": 5740000, "max": 11164400, "unit": "currency_per_event" },
  "not_good_for": "Treating the FCA penalty stress anchor as total event loss, ...",
  "provenance": {
    "frequency.min": {
      "value": 0.43,
      "source_name": "Cyber Security Breaches Survey 2025/2026",
      "url": "https://www.gov.uk/government/statistics/...",
      "publication_date": "2026-04-30",
      "confidence": "medium",
      "limitations": "UK official survey used as a bridge; not US-specific and ..."
    }
  }
}
```

`provenance` is keyed by dot-path parameter, so a consumer can render the citation next to the
input it justifies rather than as a footnote nobody reads.

The explorer page (`index.html`) reads the JSON at runtime rather than embedding a copy, which is
both the demonstration of intended use and the reason it needs a server rather than `file://`.

## Run it locally

```bash
python -m http.server 8000
```

Then open http://localhost:8000.

To regenerate the data from upstream:

```bash
pip install -r requirements.txt && git clone --depth 1 https://github.com/raviaxo/RiskShard && python build_benchmarks.py RiskShard risk-benchmarks.json
```

The build is driven by RiskShard's `risk_modules/*.yaml` manifests, which point at every other
artifact, so it resolves scenarios, calibrations and evidence by reference rather than guessing at
filenames. It reports coverage and warns on any parameter it cannot trace to a source; the current
run resolves 66 of 66 with no warnings.

## Honest limits

- **These are starting points, not benchmarks.** Read `maturity.benchmark_status` on each shard.
  Most are governed starters: the evidence is real, but the shard has not cleared human benchmark
  review. Upstream is explicit that clearing an automated gate means "review candidate", not
  "benchmark-grade", and that distinction survives into this file.
- **Some frequencies are bridged from another country.** Where no local per-firm rate is
  published, a shard borrows one that is — the US data-breach frequency comes from a UK survey,
  because the US publishes breach counts but no clean per-firm annual prevalence. Every bridged
  parameter says so in its own `limitations`.
- **Mixed measurement bases.** Within a single shard the min, likely and max can measure
  genuinely different quantities — a self-reported survey average, a claims-study mean, a single
  documented incident used as a stress anchor. That makes a range that is wider than any one
  source and not a distribution any one source would endorse.
- **Four currencies, no FX table.** Do not add shards together without converting first, and state
  the rate and date when you do. Nothing here will stop you.
- **It is a snapshot.** Generated from one upstream commit, recorded in `source.commit`. It does
  not update itself, and sources age at different rates.
- **Narrow coverage.** Four threat types, mostly financial services, mostly mid-market.
- **One AI shard, and it is the weakest thing here.** `ai_enabled_fraud` covers deepfake-enabled
  fraud only — not model failure, not prompt injection, not agentic misbehaviour. Every parameter
  is `low` confidence, the frequency counts deepfake *attempts* rather than confirmed-loss events,
  and the ceiling is one documented case (Arup, USD 25.6M) rather than a modelled percentile.
  Upstream labels it fast-rising and volatile, meaning it dates quickly. It is here because it
  clears the evidence bar, not because AI risk is well served by it: the broader public loss data
  for AI incidents does not exist in a form these gates would accept.
- **Not a substitute for your own data.** A benchmark tells you roughly where an industry sits.
  It cannot tell you where *you* sit, and the gap between those is usually the interesting part.

## Attribution

Data derived from [RiskShard](https://github.com/raviaxo/RiskShard) by
[raviaxo](https://github.com/raviaxo), AGPL-3.0 — an evidence-governed cyber risk quantification
project where every parameter traces to a reviewed public source. Figures, limitations,
calibration rationales and "not good for" statements are RiskShard's, carried through unchanged.
The flattening, the JSON schema, the build script and the explorer page are this project's own.

The shards cite 37 distinct public sources across 31 publisher domains, including the UK Cyber
Security Breaches Survey, FBI IC3, the Australian Bureau of Statistics, ACCC Scamwatch, Statistics
Canada, CNIL, Japan's National Police Agency, the Singapore Police Force, NetDiligence, Sophos,
IBM and Verizon. None are reproduced here — see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

Consumed by [risk-quantifier](https://github.com/RootCawsLLC/risk-quantifier), which loads a shard as
a starting range and renders its citations beside the inputs, and by
[loss-exceedance-curve](https://github.com/RootCawsLLC/loss-exceedance-curve), which fetches this file
at runtime and builds a curve in the shard's own currency, and by
[cyber-materiality-workbench](https://github.com/RootCawsLLC/cyber-materiality-workbench), which uses a
USD shard as a cited cross-check against a filer's own loss estimate rather than as an input.

## License

Copyright (c) 2026 RootCaws LLC.

[GNU AGPL v3 or later](LICENSE). If you modify this and run it as a network service, the AGPL
requires you to offer your users the modified source under the same terms.

The AGPL covers this project's own code and schema. The shard data originates from RiskShard, also
AGPL-3.0; the cited publications remain the property of their publishers and are referenced, not
redistributed. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
