"""SafeBIMLayer adapter and deterministic reconciliation for the executor."""
from __future__ import annotations

from typing import Any

from safe_bim_layer import SafeBIMLayer, SafeBIMError, TapirClient, _num_equal


def _items(response):
    return response.get("result", {}).get("addOnCommandResponse", {})


class SafeBIMOperations:
    def __init__(self, client: TapirClient):
        self.client = client
        self.layer = SafeBIMLayer(client)

    def current_project(self) -> str:
        path = _items(self.client.call("GetProjectInfo", {})).get("projectPath")
        if not path:
            raise SafeBIMError("GetProjectInfo returned no projectPath")
        return path

    def execute(self, operation: str, params: dict[str, Any]):
        methods = {
            "create_wall_loop": self.layer.create_wall_loop,
            "create_basic_slab": self.layer.create_basic_slab,
            "insert_window": self.layer.insert_window,
            "insert_door": self.layer.insert_door,
        }
        if operation not in methods:
            raise SafeBIMError(f"unsupported resumable operation {operation!r}")
        return methods[operation](**params)

    def _read_type(self, element_type):
        listed = self.client.call("GetElementsByType", {"elementType": element_type})
        guids = [x["elementId"]["guid"] for x in _items(listed).get("elements", [])
                 if "elementId" in x]
        if not guids:
            return []
        response = self.client.call("GetDetailsOfElements", {
            "elements": [{"elementId": {"guid": guid}} for guid in guids]})
        return list(zip(guids, _items(response).get("detailsOfElements", [])))

    @staticmethod
    def _finish(matches, expected_count):
        evidence = {"candidateGuids": [guid for guid, _ in matches],
                    "readback": [detail for _, detail in matches],
                    "status": "PASS" if len(matches) == expected_count else "UNKNOWN"}
        if len(matches) == expected_count:
            evidence["classification"] = "APPLIED"
            evidence["readbackVerified"] = True
        elif not matches:
            evidence["classification"] = "NOT_APPLIED"
        else:
            evidence["classification"] = "AMBIGUOUS"
        return evidence

    def reconcile(self, operation: str, params: dict[str, Any], _previous=None):
        if operation == "create_wall_loop":
            points = [{"x": float(p["x"]), "y": float(p["y"])}
                      for p in params["contour"]]
            if points[0] != points[-1]:
                points.append(dict(points[0]))
            expected = [(a, b) for a, b in zip(points, points[1:])]
            found = []
            for guid, detail in self._read_type("Wall"):
                actual = detail.get("details", {})
                if detail.get("floorIndex") != int(params["floor_index"]):
                    continue
                pair = (actual.get("begCoordinate"), actual.get("endCoordinate"))
                if any(pair == segment for segment in expected):
                    found.append((guid, detail))
            return self._finish(found, len(expected))
        if operation == "create_basic_slab":
            matches = []
            for guid, detail in self._read_type("Slab"):
                actual = detail.get("details", {})
                if (detail.get("floorIndex") == int(params["floor_index"])
                        and _num_equal(actual.get("thickness"), params["thickness"])
                        and actual.get("structureType") == "Basic"
                        and (_num_equal(actual.get("zCoordinate"), params["level"])
                             or _num_equal(actual.get("level"), params["level"]))):
                    matches.append((guid, detail))
            return self._finish(matches, 1)
        if operation in {"insert_window", "insert_door"}:
            element_type = "Window" if operation == "insert_window" else "Door"
            host = params["host_wall_guid"]
            intended = params["params"]
            matches = []
            for guid, detail in self._read_type(element_type):
                actual = detail.get("details", {})
                if actual.get("ownerElementId", {}).get("guid") != host:
                    continue
                if all(_num_equal(actual.get(key), intended.get(key, 0.0))
                       for key in ("centerOffset", "width", "height", "sillHeight")):
                    matches.append((guid, detail))
            return self._finish(matches, 1)
        raise SafeBIMError(f"unsupported reconciliation operation {operation!r}")
