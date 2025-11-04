# game_core.py
from enum import Enum
import time

# 상수
PREP_TIME = 60
RESOURCE_START = 5000
UNIT_COST = 100
LAND_START = 5
TAX_RATE = 10  # 의회당 초당 자원 생산
MAP_SIZE = 11  # 0~10 칸

FIELDS = ["마법", "검술", "무술", "과학기술"]
RELIGIONS = ["신앙A", "신앙B", "신앙C"]
HEROES = ["대마법사", "소드마스터", "무신", "매드 사이언티스트"]

class FacilityType(Enum):
    PINPOINT = "핀포인트"
    REPAIR = "정비소"
    TRAINING = "훈련장"
    PARLIAMENT = "의회"

class Nation:
    def __init__(self, name):
        self.name = name
        self.field = self.religion = self.hero = None
        self.resources = RESOURCE_START
        self.land = LAND_START
        self.units = []
        self.facilities = {f: False for f in FacilityType}
        self.facilities[FacilityType.PINPOINT] = True
        self.debuffs = {}
        self.border_line = 5
        self.map = [None] * MAP_SIZE  # 각 칸: {'owner': ..., 'facility': ...}
        self.last_tax_time = time.time()

    def choose_field(self, idx):    self.field = FIELDS[idx] if 0 <= idx < 4 else None
    def choose_religion(self, idx): self.religion = RELIGIONS[idx] if 0 <= idx < 3 else None
    def choose_hero(self, idx):     self.hero = HEROES[idx] if 0 <= idx < 4 else None

    def apply_buffs(self):
        buff = 1.0
        if self.field == "마법" and self.religion == "신앙A": buff *= 1.3
        if "corruption" in self.debuffs: buff *= 0.7
        return buff

    def create_unit(self, pos):
        if pos < 0 or pos >= MAP_SIZE or self.resources < UNIT_COST or not self.facilities[FacilityType.TRAINING]:
            return False
        if pos >= self.border_line:  # 적진 불가
            return False
        self.resources -= UNIT_COST
        unit = {"hp": 100, "atk": 10, "pos": pos, "level": 1}
        if self.hero == "대마법사" and self.field == "마법":
            unit["atk"] += 8
        self.units.append(unit)
        return True

    def build_facility(self, fac, pos=None):
        cost = {"정비소": 300, "훈련장": 400, "의회": 500}
        name = fac.value
        if name not in cost or self.resources < cost[name]:
            return False
        if fac == FacilityType.PINPOINT:
            return False
        self.resources -= cost[name]
        self.facilities[fac] = True
        return True

    def collect_tax(self):
        if self.facilities[FacilityType.PARLIAMENT]:
            now = time.time()
            if now - self.last_tax_time >= 1.0:
                self.resources += TAX_RATE
                self.last_tax_time = now
