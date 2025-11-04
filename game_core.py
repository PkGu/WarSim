# game_core.py
import random
from enum import Enum

# 상수
PREP_TIME = 60
RESOURCE_START = 1000
UNIT_COST = 100
LEVEL_UP_COST = 50
MAX_LEVEL = 10
LAND_START = 5

FIELDS = ["마법", "검술", "무술", "과학기술"]
RELIGIONS = ["신앙A", "신앙B", "신앙C"]
HEROES = ["대마법사", "소드마스터", "무신", "매드 사이언티스트"]

class FacilityType(Enum):
    PINPOINT = "핀포인트"
    SETPOINT = "셋포인트"
    REPAIR = "정비소"
    TRAINING = "훈련장"
    PARLIAMENT = "의회"
    TAVERN = "술집"
    HOSPITAL = "보건소"

class Nation:
    def __init__(self, name):
        self.name = name
        self.field = None
        self.religion = None
        self.hero = None
        self.resources = RESOURCE_START
        self.land = LAND_START
        self.units = []
        self.facilities = {f: False for f in FacilityType}
        self.facilities[FacilityType.PINPOINT] = True
        self.buffs = {}
        self.debuffs = {}
        self.border_line = 5

    def choose_field(self, idx):
        if 0 <= idx < len(FIELDS):
            self.field = FIELDS[idx]

    def choose_religion(self, idx):
        if 0 <= idx < len(RELIGIONS):
            self.religion = RELIGIONS[idx]

    def choose_hero(self, idx):
        if 0 <= idx < len(HEROES):
            self.hero = HEROES[idx]

    def apply_buffs(self):
        buff = 1.0
        if self.field == "마법" and self.religion == "신앙A":
            buff *= 1.3
        if 'corruption' in self.debuffs:
            buff *= 0.7
        return buff

    def create_unit(self, pos):
        if self.resources >= UNIT_COST and self.facilities[FacilityType.TRAINING]:
            self.resources -= UNIT_COST
            unit = {
                'type': 'soldier',
                'level': 1,
                'hp': 100,
                'atk': 10,
                'pos': pos
            }
            if self.hero == "대마법사" and self.field == "마법":
                unit['atk'] += 8
            self.units.append(unit)
            return True
        return False

    def build_facility(self, fac_type):
        cost = {"정비소": 300, "훈련장": 400, "의회": 500, "술집": 200, "보건소": 350}
        name = fac_type.value
        if name in cost and self.resources >= cost[name]:
            self.resources -= cost[name]
            self.facilities[fac_type] = True
            return True
        return False