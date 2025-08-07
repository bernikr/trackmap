from pathlib import Path

import geojson as gj
import overpass
import shapely


def main() -> None:
    relation_id = input("Enter relation id: ")

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
    Path(f"../tracks/{filename}").write_text(
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
    main()
