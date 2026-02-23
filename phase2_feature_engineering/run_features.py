from __future__ import annotations

"""
CLI entrypoint for Phase 2 feature engineering.

Usage:
    python -m phase2_feature_engineering.run_features
"""

from .features import generate_features_for_all, get_engine


def main() -> None:
    engine = get_engine()
    created = generate_features_for_all(engine)
    print(f"Generated features for {created} restaurants.")


if __name__ == "__main__":
    main()

