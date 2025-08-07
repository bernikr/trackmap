import json
import sys
from pathlib import Path

import geojson as gj
import overpass
import shapely

track_folder = Path(__file__).parent.parent / "tracks"
sorting_file = Path(__file__).parent / "sorting.json"

sorting = json.loads(sorting_file.read_text(encoding="utf-8")) if sorting_file.exists() else {}


def main() -> None:
    relation_id = input("Enter relation id (or 'quit'): ")

    if relation_id in {"q", "quit", "exit", "e"}:
        sys.exit()

    if not relation_id.isdigit():
        print("invalid relation id")
        return

    print("downloading relation")
    api = overpass.API()
    response: dict = api.get(f"rel({relation_id})", responseformat="json", verbosity="geom")  # type: ignore

    print("processing relation")

    assert len(response["elements"]) == 1
    line = shapely.MultiLineString(
        [
            [[c["lon"], c["lat"]] for c in m["geometry"]]
            for m in response["elements"][0]["members"]
            if m["type"] == "way" and not m["role"]
        ],
    )

    line = shapely.line_merge(line)
    if isinstance(line, shapely.MultiLineString):
        print("WARNING: cant simplify relation to single line")
        geom = gj.MultiLineString([list(l.coords) for l in line.geoms])
    elif isinstance(line, shapely.LineString):
        geom = gj.LineString(list(line.coords))
    else:
        msg = f"Unknown type: {type(line)}"
        raise TypeError(msg)

    tags = response["elements"][0]["tags"]
    if "from" in tags or "to" in tags:
        filename = f"{relation_id}-{tags.get('ref')}-{tags.get('from')}-{tags.get('to')}.geojson"
    else:
        filename = f"{relation_id}-{tags.get('ref')}-{tags.get('name')}.geojson"

    operator = tags.get("operator")
    if operator:
        if operator not in sorting:
            print(f"new operator: {operator}")
            folder = input("Enter folder name: ")
            sorting[operator] = folder
            sorting_file.write_text(json.dumps(sorting, indent=2), encoding="utf-8")
        if sorting[operator]:
            filename = f"{sorting[operator]}/{filename}"

    outfile = track_folder / filename
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(
        gj.dumps(
            gj.FeatureCollection(
                [
                    gj.Feature(
                        geometry=geom,
                        properties={
                            "id": relation_id,
                            **tags,
                        },
                    ),
                ],
            ),
        ),
        encoding="utf-8",
    )
    print(f"saved to {filename}")


if __name__ == "__main__":
    while True:
        main()
