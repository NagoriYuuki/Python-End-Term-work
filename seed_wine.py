"""
Seed Wine table from sklearn.datasets.load_wine into MySQL via Flask-SQLAlchemy.

- Auto get-or-create an ImportBatch with source="sklearn"
- Insert 178 rows into Wine, with batch_id set (referential integrity)

Usage:
  python seed_wine.py
  python seed_wine.py --reset
"""

from __future__ import annotations

import argparse

from sklearn.datasets import load_wine

from app import app, db
from models import ImportBatch, Wine


def get_or_create_batch(source: str, note: str | None = None) -> ImportBatch:
    batch = (
        ImportBatch.query.filter_by(source=source)
        .order_by(ImportBatch.id.desc())
        .first()
    )
    if batch is None:
        batch = ImportBatch(source=source)
        db.session.add(batch)
        db.session.commit()  # 必须先提交，batch.id 才会有值
    return batch


def seed(reset: bool = False) -> int:
    dataset = load_wine()
    name_to_index = {name: idx for idx, name in enumerate(dataset.feature_names)}

    required = ["alcohol", "malic_acid", "color_intensity"]
    missing = [name for name in required if name not in name_to_index]
    if missing:
        raise RuntimeError(f"load_wine missing required features: {missing}")

    with app.app_context():
        db.create_all()

        if reset:
            # 先删子表 Wine，再删/不删 ImportBatch 都行
            db.session.query(Wine).delete()
            db.session.commit()

        batch = get_or_create_batch(source="sklearn")

        rows: list[Wine] = []
        for features, target in zip(dataset.data, dataset.target):
            rows.append(
                Wine(
                    alcohol=float(features[name_to_index["alcohol"]]),
                    malic_acid=float(features[name_to_index["malic_acid"]]),
                    color_intensity=float(features[name_to_index["color_intensity"]]),
                    target=int(target),      # 0/1/2
                    batch_id=batch.id,       # 关键：外键指向 ImportBatch
                )
            )

        db.session.bulk_save_objects(rows)
        db.session.commit()
        return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing Wine rows before inserting.",
    )
    args = parser.parse_args()

    inserted = seed(reset=args.reset)
    print(f"Inserted {inserted} rows into Wine")


if __name__ == "__main__":
    main()