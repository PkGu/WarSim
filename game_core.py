# server/game_core.py
import json

class Nation:
    def __init__(self, name):
        self.name = name
        self.gold = 1000
        self.units = []
        self.has_parliament = False

    def build_parliament(self):
        """의회는 한 번만 지을 수 있다."""
        if self.has_parliament:
            return {"status": "fail", "reason": "already_built"}
        cost = 300
        if self.gold >= cost:
            self.gold -= cost
            self.has_parliament = True
            return {"status": "success", "action": "parliament_built"}
        return {"status": "fail", "reason": "not_enough_gold"}

    def create_unit(self):
        """유닛 생성: 의회가 있어야 가능"""
        if not self.has_parliament:
            return {"status": "fail", "reason": "no_parliament"}
        cost = 100
        if self.gold >= cost:
            self.gold -= cost
            unit = {"id": len(self.units) + 1, "hp": 100}
            self.units.append(unit)
            return {"status": "success", "action": "unit_created", "unit": unit}
        return {"status": "fail", "reason": "not_enough_gold"}

    def to_dict(self):
        return {
            "name": self.name,
            "gold": self.gold,
            "units": self.units,
            "has_parliament": self.has_parliament
        }

# helper
def encode_state(nation):
    return json.dumps({"type": "update", "state": nation.to_dict()})
