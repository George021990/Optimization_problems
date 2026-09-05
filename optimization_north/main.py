"""Запуск тестового экземпляра оптимизационной модели (Север)."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .data import make_test_instance
from .model import extract_schedule, objective_breakdown, solve_model


def _print_table(rows: list[dict]) -> None:
    if not rows:
        return
    headers = list(rows[0].keys())
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}
    line = " | ".join(h.ljust(widths[h]) for h in headers)
    sep = "-+-".join("-" * widths[h] for h in headers)
    print(line)
    print(sep)
    for row in rows:
        print(" | ".join(str(row[h]).ljust(widths[h]) for h in headers))


def _print_repair_schedule(data) -> None:
    print("Входной график ремонта:")
    if not data.repair_schedule:
        print("  нет назначенных ремонтов")
        return
    for window in data.repair_schedule:
        last = window.start_day + window.duration - 1
        print(
            "  {vid}: {port}, дни {start}-{end} (длительность {dur})".format(
                vid=window.vessel_id,
                port=window.port,
                start=window.start_day,
                end=last,
                dur=window.duration,
            )
        )


def run(time_limit: int = 30, output: str | None = None, quiet: bool = False) -> int:
    data = make_test_instance()
    print("Тестовый экземпляр: Север, горизонт {} дней, судов: {}.".format(
        len(data.days), len(data.vessels)
    ))
    _print_repair_schedule(data)
    model, extras, status = solve_model(data, time_limit=time_limit, msg=not quiet)
    print(f"Статус решателя: {status}")
    if status not in {"Optimal", "Feasible"}:
        print("Допустимое решение не найдено.")
        return 1

    breakdown = objective_breakdown(extras)
    print("\nКомпоненты целевой функции, руб.:")
    for name, value in breakdown.items():
        print(f"  {name:<24} {value:>14,.0f}")

    rows = extract_schedule(data, extras)
    print("\nКалендарный график:")
    _print_table(rows)

    out_path = Path(output) if output else Path(__file__).resolve().parent / "schedule.csv"
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nГрафик сохранён в {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Оптимизационная модель календарного планирования флота (Север)."
    )
    parser.add_argument("--time-limit", type=int, default=30, help="Лимит времени CBC, сек.")
    parser.add_argument("--output", type=str, default=None, help="Путь к CSV с графиком.")
    parser.add_argument("--quiet", action="store_true", help="Не печатать лог CBC.")
    args = parser.parse_args(argv)
    return run(time_limit=args.time_limit, output=args.output, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
