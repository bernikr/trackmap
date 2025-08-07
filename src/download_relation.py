import sys
from pathlib import Path

import geojson as gj
import overpass
import shapely


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

    filename = f"{relation_id}-{response['elements'][0]['tags'].get('ref')}.geojson"
    operator = response["elements"][0]["tags"].get("operator")
    if operator:
        filename = f"{operator}/{filename}"
    outfile = Path(f"../tracks/{filename}")
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(
        gj.dumps(
            gj.FeatureCollection(
                [
                    gj.Feature(
                        geometry=geom,
                        properties={
                            "id": relation_id,
                            "type": "relation",
                            "tags": response["elements"][0]["tags"],
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
