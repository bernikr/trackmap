from pathlib import Path

import geojson as gj

track_folder = Path(__file__).parent.parent / "tracks"


def main() -> None:
    features = []
    for f in track_folder.glob("**/*.geojson"):
        geom = gj.loads(f.read_text(encoding="utf-8"))
        if not isinstance(geom, gj.FeatureCollection):
            print(f"skipping {f}: not a feature collection")
            continue
        features.extend(geom["features"])
    Path("../out.geojson").write_text(gj.dumps(gj.FeatureCollection(features)), encoding="utf-8")


if __name__ == "__main__":
    main()
