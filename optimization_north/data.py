"""Тестовый экземпляр оптимизационной модели (Север)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Set, Tuple


Location = str
VesselId = str
SpeciesId = str
ProductId = str


@dataclass(frozen=True)
class Vessel:
    id: VesselId
    name: str
    kind: str  # LIVE_CRAB_CARRIER | PROCESSOR | TRANSPORT
    hold_capacity: float
    voyage_limit: int
    initial_location: Location
    initial_hold: float
    daily_fixed_cost: float
    crew_salary: float
    daily_catch: Dict[Tuple[SpeciesId, Location], float] = field(default_factory=dict)


@dataclass(frozen=True)
class RepairWindow:
    """Входной слот ремонта: судно обязано быть в указанном порту все дни окна."""

    vessel_id: VesselId
    port: Location
    start_day: int
    duration: int

    def days(self) -> List[int]:
        return list(range(self.start_day, self.start_day + self.duration))


@dataclass
class TestInstance:
    """Компактный, но полный набор множеств и параметров из документа."""

    days: List[int]
    zones: List[Location]
    ports: List[Location]
    vessels: List[Vessel]
    species: List[SpeciesId]
    products: List[ProductId]
    product_of_species: Dict[SpeciesId, ProductId]
    yield_coef: Dict[Tuple[SpeciesId, ProductId], float]
    price: Dict[ProductId, float]
    quota_max: Dict[SpeciesId, float]
    quota_min: Dict[SpeciesId, float]
    travel_time: Dict[Tuple[Location, Location], int]
    fuel_cost: Dict[str, float]
    production_cost: Dict[ProductId, float]
    container_cost: Dict[ProductId, float]
    port_entry_cost: Dict[Location, float]
    port_idle_cost: Dict[Location, float]
    port_repair_cost: Dict[Location, float]
    crew_commission: float
    fishing_allowed: Set[Tuple[VesselId, Location, int]]
    repair_schedule: List[RepairWindow]
    repair_days: Set[Tuple[VesselId, Location, int]]

    @property
    def locations(self) -> List[Location]:
        return list(self.ports) + list(self.zones)

    @property
    def arcs(self) -> List[Tuple[Location, Location]]:
        return [(i, j) for (i, j) in self.travel_time.keys()]

    def vessels_of(self, kind: str) -> List[Vessel]:
        return [v for v in self.vessels if v.kind == kind]

    def vessel_map(self) -> Dict[VesselId, Vessel]:
        return {v.id: v for v in self.vessels}

    def neighbors(self, origin: Location) -> Iterable[Location]:
        for i, j in self.arcs:
            if i == origin:
                yield j

    def is_repair_day(self, vessel_id: VesselId, day: int) -> bool:
        return any(v == vessel_id and t == day for v, _port, t in self.repair_days)

    def repair_port(self, vessel_id: VesselId, day: int) -> Location | None:
        for v, port, t in self.repair_days:
            if v == vessel_id and t == day:
                return port
        return None


def expand_repair_days(
    schedule: Sequence[RepairWindow],
    days: Sequence[int],
) -> Set[Tuple[VesselId, Location, int]]:
    day_set = set(days)
    result: Set[Tuple[VesselId, Location, int]] = set()
    for window in schedule:
        if window.duration <= 0:
            raise ValueError(f"Длительность ремонта должна быть положительной: {window}")
        for t in window.days():
            if t in day_set:
                result.add((window.vessel_id, window.port, t))
    return result


def _full_mesh(nodes: Sequence[Location], time: int) -> Dict[Tuple[Location, Location], int]:
    times: Dict[Tuple[Location, Location], int] = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                times[(i, j)] = time
    return times


def make_test_instance() -> TestInstance:
    """
    Небольшой северный сценарий на 8 суток:

    * 1 порт (Петропавловск), 2 зоны промысла;
    * 1 краболов (V1), 1 процессор (V2), 1 транспортник (V3);
    * 1 вид краба и 2 типа продукции (живой / варёно-мороженый);
    * входной график ремонта: V1 дни 7–8, V2 день 8.
    """
    days = list(range(1, 9))
    zones = ["Зона-Запад", "Зона-Восток"]
    ports = ["Петропавловск"]
    locations = ports + zones

    species = ["камчатский краб"]
    live = "живой краб"
    frozen = "варено-мороженый краб"
    products = [live, frozen]

    v1 = Vessel(
        id="V1",
        name="Камчатка-1",
        kind="LIVE_CRAB_CARRIER",
        hold_capacity=40.0,
        voyage_limit=6,
        initial_location="Петропавловск",
        initial_hold=0.0,
        daily_fixed_cost=180_000.0,
        crew_salary=90_000.0,
        daily_catch={("камчатский краб", "Зона-Запад"): 12.0, ("камчатский краб", "Зона-Восток"): 10.0},
    )
    v2 = Vessel(
        id="V2",
        name="Процессор-1",
        kind="PROCESSOR",
        hold_capacity=28.0,
        voyage_limit=7,
        initial_location="Петропавловск",
        initial_hold=0.0,
        daily_fixed_cost=260_000.0,
        crew_salary=120_000.0,
        daily_catch={("камчатский краб", "Зона-Запад"): 14.0, ("камчатский краб", "Зона-Восток"): 16.0},
    )
    v3 = Vessel(
        id="V3",
        name="Транспорт-1",
        kind="TRANSPORT",
        hold_capacity=50.0,
        voyage_limit=6,
        initial_location="Петропавловск",
        initial_hold=0.0,
        daily_fixed_cost=150_000.0,
        crew_salary=70_000.0,
        daily_catch={},
    )

    repair_schedule = [
        RepairWindow(vessel_id="V1", port="Петропавловск", start_day=7, duration=2),
        RepairWindow(vessel_id="V2", port="Петропавловск", start_day=8, duration=1),
    ]
    repair_days = expand_repair_days(repair_schedule, days)
    vessels_in_repair = {(v, t) for v, _port, t in repair_days}

    fishing_allowed = {
        (v.id, zone, t)
        for v in (v1, v2)
        for zone in zones
        for t in days
        if (v.id, t) not in vessels_in_repair
    }

    return TestInstance(
        days=days,
        zones=zones,
        ports=ports,
        vessels=[v1, v2, v3],
        species=species,
        products=products,
        product_of_species={"камчатский краб": live},
        yield_coef={
            ("камчатский краб", live): 1.0,
            ("камчатский краб", frozen): 0.65,
        },
        price={live: 1_200_000.0, frozen: 1_800_000.0},
        quota_max={"камчатский краб": 180.0},
        quota_min={"камчатский краб": 0.0},
        travel_time=_full_mesh(locations, time=1),
        fuel_cost={"fishing": 70_000.0, "transit": 95_000.0, "port": 15_000.0},
        production_cost={live: 0.0, frozen: 80_000.0},
        container_cost={live: 5_000.0, frozen: 12_000.0},
        port_entry_cost={"Петропавловск": 120_000.0},
        port_idle_cost={"Петропавловск": 40_000.0},
        port_repair_cost={"Петропавловск": 200_000.0},
        crew_commission=0.08,
        fishing_allowed=fishing_allowed,
        repair_schedule=repair_schedule,
        repair_days=repair_days,
    )
