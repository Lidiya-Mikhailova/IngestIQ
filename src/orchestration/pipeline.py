from __future__ import annotations

from src.ingest.run import run_all, OneSourceResult


def _print_result(r: OneSourceResult) -> None:
    if r.status == "ok":
        print(f"OK   {r.source} {r.dataset}: rows={r.rows} raw={r.raw_path} reason={r.reason}")
    elif r.status == "skipped":
        print(f"SKIP {r.source} {r.dataset}: {r.reason}")
    else:
        print(f"FAIL {r.source} {r.dataset}: {r.reason}")


def run_pipeline(*, full_refresh: bool = False) -> list[OneSourceResult]:
    print("Pipeline started")

    results = run_all(full_refresh=full_refresh)
    for r in results:
        _print_result(r)

    total = len(results)
    ok = sum(1 for r in results if r.status == "ok")
    skipped = sum(1 for r in results if r.status == "skipped")
    failed = sum(1 for r in results if r.status == "failed")

    print(f"Pipeline summary: total={total}, ok={ok}, skipped={skipped}, failed={failed}")
    print("Pipeline finished")

    return results


if __name__ == "__main__":
    run_pipeline()
