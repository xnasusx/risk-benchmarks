"""Flatten RiskShard's governed shards into a single JSON for browser tools.

Driven by risk_modules/*.yaml (the shard manifest), which points at every other
artifact, so nothing here guesses at filenames. Parameters are joined to their
citation via calibrations -> evidence_id -> evidence records, falling back to a
dot-path match against the evidence record's own `parameter` field.
"""
import glob
import json
import os
import subprocess
import sys

import yaml

SRC = sys.argv[1]
OUT = sys.argv[2]
PARAMS = ["frequency.min", "frequency.likely", "frequency.max",
          "impact.min", "impact.likely", "impact.max"]


def load(rel):
    p = os.path.join(SRC, rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def dig(d, dotted):
    cur = d
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def evidence_index(paths):
    """id -> record, and dot-path -> record (first wins)."""
    by_id, by_param = {}, {}
    for rel in paths or []:
        doc = load(rel) or {}
        for rec in doc.get("records", []) or []:
            if rec.get("id"):
                by_id[rec["id"]] = rec
            if rec.get("parameter") and rec["parameter"] not in by_param:
                by_param[rec["parameter"]] = rec
    return by_id, by_param


def citation(rec, cal_entry):
    """Normalise one evidence record + its calibration note into a citation."""
    out = {}
    if cal_entry:
        out["rationale"] = cal_entry.get("rationale")
        out["transform"] = cal_entry.get("transform")
    if rec:
        out.update({
            "evidence_id": rec.get("id"),
            "source_name": rec.get("source_name"),
            "source_type": rec.get("source_type"),
            "url": rec.get("source_url_or_citation"),
            "publication_date": str(rec.get("publication_date") or "") or None,
            "citation_detail": rec.get("citation_detail"),
            "limitations": rec.get("limitations"),
            "confidence": rec.get("confidence"),
            "evidence_type": rec.get("evidence_type"),
            "measurement_basis": rec.get("measurement_basis"),
        })
    return {k: v for k, v in out.items() if v not in (None, "")}


def display_fields(b):
    """Canonical display strings, computed once here rather than reimplemented
    (and broken on nulls) in each consuming tool. A promoted shard has no
    country or sector, and 'null - undefined' is not an acceptable option label.
    """
    nice = lambda s: (s or "").replace("_", " ")
    b["label"] = f'{b["country"]} · {b["title"]}' if b.get("country") else b["title"]
    parts = [b["country"] or "no country stated",
             nice(b.get("industry")) or "no sector stated",
             nice(b.get("threat")) or "unclassified"]
    b["scope"] = " · ".join(parts)
    return b


def confidence_summary(prov):
    """How many parameters sit at each confidence level. A shard where every
    parameter is 'low' should not read the same as one where they are 'high'."""
    out = {}
    for c in prov.values():
        k = c.get("confidence") or "unstated"
        out[k] = out.get(k, 0) + 1
    return out


def build_promoted(scen_rel, warnings):
    """A scenario with no risk_module can still be fully sourced.

    Upstream, a module is the manifest that ties a scenario to an org profile, a
    calibration and its evidence. Some scenarios carry evidence records without
    that wrapper -- notably the only AI-relevant shard. Dropping them threw away
    real provenance, so they are admitted on the same evidence bar the governed
    shards clear (complete triangle, all six parameters traced to a
    source_backed record) and labelled a weaker tier rather than silently mixed
    in: no calibration rationale, no practitioner review, no 'not good for'.
    """
    scen = load(scen_rel)
    if not scen:
        return None
    name = os.path.basename(scen_rel)[:-5]
    _, by_param = evidence_index(["evidence/%s.yaml" % name])
    if not by_param:
        return None

    prov = {}
    for p in PARAMS:
        if dig(scen, p) is None:
            return None
        rec = by_param.get(p)
        if not rec or rec.get("evidence_type") != "source_backed":
            return None
        c = citation(rec, None)
        c["value"] = dig(scen, p)
        prov[p] = c

    meta = scen.get("metadata", {}) or {}
    warnings.append(f"{name}: promoted without a risk_module (evidence_backed tier)")
    return {
        "id": name,
        "title": meta.get("name") or name,
        "threat": name,
        "status": meta.get("scenario_stage"),
        "provenance_tier": "evidence_backed",
        "confidence_summary": confidence_summary(prov),
        "country": None,
        "industry": None,
        "company_size": None,
        "currency": meta.get("currency"),
        "maturity": {
            "scenario_stage": meta.get("scenario_stage"),
            "benchmark_status": meta.get("benchmark_status"),
        },
        "description": (meta.get("description") or "").strip() or None,
        "frequency": {**scen.get("frequency", {}), "unit": "events_per_year"},
        "impact": {**scen.get("impact", {}), "unit": "currency_per_event"},
        "loss_stages": scen.get("loss_stages") or [],
        "org_profile": None,
        "not_good_for": None,
        "good_for": None,
        "tags": [],
        "provenance": prov,
        "sourced_parameters": len(prov),
        "total_parameters": len(prov),
        "source_files": {"module": None, "scenario": scen_rel, "calibration": None,
                         "evidence": ["evidence/%s.yaml" % name]},
    }


def build_shard(mod_path, warnings):
    mod = load(os.path.relpath(mod_path, SRC))
    art = mod.get("artifacts", {}) or {}
    scen = load(art.get("scenario") or "")
    if not scen:
        warnings.append(f"{mod['id']}: scenario missing ({art.get('scenario')})")
        return None
    cal = load(art.get("calibration") or "") or {}
    org = load(art.get("org_profile") or "") or {}
    by_id, by_param = evidence_index(art.get("evidence"))

    meta = scen.get("metadata", {}) or {}
    prov, sourced = {}, 0
    for p in PARAMS:
        if dig(scen, p) is None:
            continue
        cal_entry = dig(cal, "parameters." + p) or {}
        rec = by_id.get(cal_entry.get("evidence_id")) or by_param.get(p)
        c = citation(rec, cal_entry)
        c["value"] = dig(scen, p)
        if c.get("evidence_type") == "source_backed":
            sourced += 1
        elif not rec:
            warnings.append(f"{mod['id']}: no evidence record for {p}")
        prov[p] = c

    ctx = mod.get("context", {}) or {}
    return {
        "id": mod.get("id"),
        "title": mod.get("title"),
        "threat": mod.get("threat"),
        "status": mod.get("status"),
        "provenance_tier": "module_governed",
        "confidence_summary": confidence_summary(prov),
        "country": ctx.get("country"),
        "industry": ctx.get("industry"),
        "company_size": ctx.get("company_size"),
        "currency": meta.get("currency") or cal.get("target_currency"),
        "maturity": {
            "scenario_stage": meta.get("scenario_stage"),
            "benchmark_status": meta.get("benchmark_status"),
        },
        "description": (meta.get("description") or "").strip() or None,
        "frequency": {**scen.get("frequency", {}), "unit": "events_per_year"},
        "impact": {**scen.get("impact", {}), "unit": "currency_per_event"},
        "loss_stages": scen.get("loss_stages") or [],
        "org_profile": {
            "employees": org.get("employees"),
            "annual_revenue_or_budget": org.get("annual_revenue_or_budget"),
            "regulatory_intensity": org.get("regulatory_intensity"),
        } if org else None,
        "not_good_for": (mod.get("practitioner_notes", {}) or {}).get("not_good_for"),
        "good_for": (mod.get("practitioner_notes", {}) or {}).get("good_for"),
        "tags": mod.get("tags") or [],
        "provenance": prov,
        "sourced_parameters": sourced,
        "total_parameters": len(prov),
        "source_files": {
            "module": os.path.relpath(mod_path, SRC).replace("\\", "/"),
            "scenario": art.get("scenario"),
            "calibration": art.get("calibration"),
            "evidence": art.get("evidence") or [],
        },
    }


def main():
    warnings = []
    shards = []
    for mp in sorted(glob.glob(os.path.join(SRC, "risk_modules", "*.yaml"))):
        s = build_shard(mp, warnings)
        if s:
            shards.append(s)

    # Scenario files not claimed by any module. Fully sourced ones are promoted
    # into benchmarks at the weaker tier; the rest are demo fixtures and worked
    # examples with no provenance at all.
    claimed = {s["source_files"]["scenario"] for s in shards}
    for sp in sorted(glob.glob(os.path.join(SRC, "scenarios", "*.yaml"))):
        rel = "scenarios/" + os.path.basename(sp)
        if rel in claimed:
            continue
        p = build_promoted(rel, warnings)
        if p:
            shards.append(p)
            claimed.add(rel)

    examples = []
    for sp in sorted(glob.glob(os.path.join(SRC, "scenarios", "*.yaml"))):
        rel = "scenarios/" + os.path.basename(sp)
        if rel in claimed:
            continue
        doc = load(rel) or {}
        meta = doc.get("metadata", {}) or {}
        examples.append({
            "id": os.path.basename(sp)[:-5],
            "title": meta.get("name"),
            "currency": meta.get("currency"),
            "maturity": {
                "scenario_stage": meta.get("scenario_stage"),
                "benchmark_status": meta.get("benchmark_status"),
            },
            "description": (meta.get("description") or "").strip() or None,
            "frequency": doc.get("frequency") or {},
            "impact": doc.get("impact") or {},
            "loss_stages": doc.get("loss_stages") or [],
            "provenance": None,
            "source_files": {"scenario": rel},
        })

    shards = [display_fields(s) for s in shards]

    sha = subprocess.run(["git", "-C", SRC, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    out = {
        "schema_version": "1.0",
        "source": {
            "repo": "https://github.com/raviaxo/RiskShard",
            "commit": sha,
            "license": "AGPL-3.0-or-later",
        },
        "tiers": {
            "module_governed": "Upstream carries a risk_module manifest tying the scenario to an "
                               "org profile, a calibration record and its evidence, plus a "
                               "practitioner statement of what it is not good for.",
            "evidence_backed": "Every parameter traces to a source_backed evidence record on the "
                               "same bar, but there is no module manifest: no calibration "
                               "rationale, no practitioner review, and no stated not_good_for. "
                               "Read confidence_summary before using one.",
        },
        "usage_notes": [
            "Every number here is a starting point, not a benchmark. Check maturity.benchmark_status.",
            "Check provenance_tier. evidence_backed shards clear the same evidence bar but carry no practitioner review.",
            "confidence_summary counts parameters by confidence level; a shard that is all-low is not a benchmark.",
            "not_good_for states, per shard, what the numbers will not support.",
            "provenance is keyed by dot-path parameter; each entry carries its own source and limitations.",
            "Currencies differ across shards. Do not aggregate without converting first.",
            "Entries under `examples` have no provenance and are illustrative only.",
        ],
        "benchmarks": shards,
        "examples": examples,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    tot = sum(s["total_parameters"] for s in shards)
    src = sum(s["sourced_parameters"] for s in shards)
    print(f"benchmarks={len(shards)} examples={len(examples)}")
    print(f"parameters={tot} source_backed={src} ({100*src//max(tot,1)}%)")
    print(f"bytes={os.path.getsize(OUT)}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print("  " + w)


main()
