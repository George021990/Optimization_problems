"""MILP календарного планирования расстановки флота (Север)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pulp

from .data import Location, TestInstance, Vessel, VesselId


def build_model(data: TestInstance) -> Tuple[pulp.LpProblem, Dict[str, Any]]:
    """Строит модель в соответствии с разделами 5–9 документа."""
    T = data.days
    K = data.locations
    F = data.zones
    S = data.ports
    G = data.species
    vessels = data.vessels
    V = [v.id for v in vessels]
    vm = data.vessel_map()
    V1 = [v.id for v in data.vessels_of("LIVE_CRAB_CARRIER")]
    V2 = [v.id for v in data.vessels_of("PROCESSOR")]
    V3 = [v.id for v in data.vessels_of("TRANSPORT")]
    catchers = V1 + V2
    carriers = V1 + V3
    arcs = data.arcs
    tau = data.travel_time
    cap = {v.id: v.hold_capacity for v in vessels}

    m = pulp.LpProblem("north_fleet_scheduling", pulp.LpMaximize)

    loc = pulp.LpVariable.dicts("loc", (V, K, T), cat="Binary")
    start = pulp.LpVariable.dicts("start", (V, K, K, T), cat="Binary")
    in_tr = pulp.LpVariable.dicts("in_tr", (V, T), cat="Binary")
    fish = pulp.LpVariable.dicts("fish", (V, T), cat="Binary")
    transfer = pulp.LpVariable.dicts("transfer", (V, T), cat="Binary")
    repair = pulp.LpVariable.dicts("repair", (V, S, T), cat="Binary")
    idle = pulp.LpVariable.dicts("idle", (V, S, T), cat="Binary")
    unload_bin = pulp.LpVariable.dicts("unload_bin", (V, S, T), cat="Binary")
    entry = pulp.LpVariable.dicts("entry", (V, S, T), lowBound=0, upBound=1, cat="Continuous")
    meet = pulp.LpVariable.dicts("meet", (V2, V3, T), cat="Binary")
    meet_z = pulp.LpVariable.dicts("meet_z", (V2, V3, F, T), cat="Binary")

    x = pulp.LpVariable.dicts("catch", (catchers, G, F, T), lowBound=0, cat="Continuous")
    y = pulp.LpVariable.dicts("prod", (V2, data.products, F, T), lowBound=0, cat="Continuous")
    H = pulp.LpVariable.dicts("hold", (V, T), lowBound=0, cat="Continuous")
    U = pulp.LpVariable.dicts("unload", (carriers, S, T), lowBound=0, cat="Continuous")
    Q = pulp.LpVariable.dicts("transship", (V2, V3, T), lowBound=0, cat="Continuous")

    def loc_prev(v: VesselId, k: Location, t: int) -> Any:
        if t == T[0]:
            return 1 if vm[v].initial_location == k else 0
        return loc[v][k][t - 1]

    def hold_prev(v: VesselId, t: int) -> Any:
        if t == T[0]:
            return vm[v].initial_hold
        return H[v][t - 1]

    # Переход только по допустимой дуге.
    for v in V:
        for i in K:
            for j in K:
                for t in T:
                    if (i, j) not in tau:
                        m += start[v][i][j][t] == 0

    # Не более одного перехода в день; старт только из фактической локации.
    for v in V:
        for t in T:
            m += pulp.lpSum(start[v][i][j][t] for i, j in arcs) <= 1
            for i, j in arcs:
                m += start[v][i][j][t] <= loc_prev(v, i, t)

    # Баланс местоположения и пребывание в пути.
    for v in V:
        for t in T:
            covering = []
            for i, j in arcs:
                dur = tau[(i, j)]
                for t0 in T:
                    if t0 <= t <= t0 + dur - 1:
                        covering.append(start[v][i][j][t0])
            m += in_tr[v][t] == pulp.lpSum(covering)
            m += pulp.lpSum(loc[v][k][t] for k in K) + in_tr[v][t] == 1

        for k in K:
            for t in T:
                departures = pulp.lpSum(start[v][k][j][t] for j in K if (k, j) in tau)
                arrivals = []
                for i in K:
                    if (i, k) not in tau:
                        continue
                    dur = tau[(i, k)]
                    t0 = t - dur
                    if t0 in T:
                        arrivals.append(start[v][i][k][t0])
                m += loc[v][k][t] == loc_prev(v, k, t) - departures + pulp.lpSum(arrivals)

    # Портовые подрежимы: ремонт / стоянка / отгрузка.
    # График ремонта — входные данные: в эти дни судно только в заданном порту.
    repair_index = {(v_id, t): port for v_id, port, t in data.repair_days}
    for v in V:
        for t in T:
            planned_port = repair_index.get((v, t))
            if planned_port is not None:
                m += loc[v][planned_port][t] == 1
                m += repair[v][planned_port][t] == 1
                m += in_tr[v][t] == 0
                m += fish[v][t] == 0
                m += transfer[v][t] == 0
                m += pulp.lpSum(start[v][i][j][t] for i, j in arcs) == 0
                for s in S:
                    if s != planned_port:
                        m += loc[v][s][t] == 0
                        m += repair[v][s][t] == 0
            else:
                for s in S:
                    m += repair[v][s][t] == 0

        for s in S:
            for t in T:
                m += repair[v][s][t] + idle[v][s][t] + unload_bin[v][s][t] == loc[v][s][t]
                m += entry[v][s][t] >= loc[v][s][t] - loc_prev(v, s, t)
                if v in V3:
                    m += idle[v][s][t] == 0

    # Переход не может пересекать заранее заданные дни ремонта.
    for v in V:
        for i, j in arcs:
            dur = tau[(i, j)]
            for t0 in T:
                occupied = [t0 + k for k in range(dur) if (t0 + k) in T]
                if any((v, t) in repair_index for t in occupied):
                    m += start[v][i][j][t0] == 0

    # Иерархия состояний в зоне промысла.
    for v in V:
        for t in T:
            in_zone = pulp.lpSum(loc[v][f][t] for f in F)
            in_port = pulp.lpSum(loc[v][s][t] for s in S)
            m += fish[v][t] <= in_zone
            if v in V1:
                m += fish[v][t] == in_zone
                m += transfer[v][t] == 0
            elif v in V2:
                m += fish[v][t] + transfer[v][t] == in_zone
            elif v in V3:
                m += fish[v][t] == 0
                m += transfer[v][t] == in_zone
            m += in_port + in_zone + in_tr[v][t] == 1

    # Вылов только в режиме промысла и в допустимом окне.
    for v in catchers:
        vessel = vm[v]
        for g in G:
            for f in F:
                rate = vessel.daily_catch.get((g, f), 0.0)
                for t in T:
                    allowed = 1 if (v, f, t) in data.fishing_allowed and rate > 0 else 0
                    m += x[v][g][f][t] <= rate * fish[v][t]
                    m += x[v][g][f][t] <= rate * loc[v][f][t]
                    m += x[v][g][f][t] <= rate * allowed

    # Выпуск продукции процессором: сырьё распределяется по видам продукции.
    processor_products = [p for p in data.products if p != data.product_of_species[data.species[0]]]
    if not processor_products:
        processor_products = list(data.products)
    for v in V2:
        for p in data.products:
            for f in F:
                for t in T:
                    if p not in processor_products:
                        m += y[v][p][f][t] == 0
                    else:
                        m += y[v][p][f][t] <= pulp.lpSum(
                            data.yield_coef.get((g, p), 0.0) * x[v][g][f][t] for g in G
                        )
        for g in G:
            for f in F:
                for t in T:
                    terms = []
                    for p in processor_products:
                        coef = data.yield_coef.get((g, p), 0.0)
                        if coef > 0:
                            terms.append(y[v][p][f][t] * (1.0 / coef))
                    if terms:
                        m += pulp.lpSum(terms) <= x[v][g][f][t]

    # Квоты.
    for g in G:
        total = pulp.lpSum(x[v][g][f][t] for v in catchers for f in F for t in T)
        m += total <= data.quota_max[g]
        m += total >= data.quota_min[g]

    # Вместимость трюма.
    for v in V:
        for t in T:
            m += H[v][t] <= cap[v]

    # Баланс трюма V1: вылов минус выгрузка в порту.
    for v in V1:
        for t in T:
            catch_t = pulp.lpSum(x[v][g][f][t] for g in G for f in F)
            unload_t = pulp.lpSum(U[v][s][t] for s in S)
            m += H[v][t] == hold_prev(v, t) + catch_t - unload_t

    # Баланс процессора: выпуск минус передача транспортнику.
    for v in V2:
        for t in T:
            prod_t = pulp.lpSum(y[v][p][f][t] for p in data.products for f in F)
            sent_t = pulp.lpSum(Q[v][w][t] for w in V3)
            m += H[v][t] == hold_prev(v, t) + prod_t - sent_t

    # Баланс транспортника: приём от процессора минус выгрузка в порту.
    for w in V3:
        for t in T:
            recv_t = pulp.lpSum(Q[v][w][t] for v in V2)
            unload_t = pulp.lpSum(U[w][s][t] for s in S)
            m += H[w][t] == hold_prev(w, t) + recv_t - unload_t

    # Выгрузка только в порту и только в режиме отгрузки.
    for v in carriers:
        for s in S:
            for t in T:
                m += U[v][s][t] <= hold_prev(v, t)
                m += U[v][s][t] <= cap[v] * unload_bin[v][s][t]
                m += U[v][s][t] <= cap[v] * loc[v][s][t]

    # Перегрузка процессор -> транспортник в одной зоне в один день.
    for v in V2:
        for w in V3:
            for t in T:
                m += meet[v][w][t] == pulp.lpSum(meet_z[v][w][f][t] for f in F)
                m += meet[v][w][t] <= transfer[v][t]
                m += meet[v][w][t] <= transfer[w][t]
                m += Q[v][w][t] <= min(cap[v], cap[w]) * meet[v][w][t]
                m += Q[v][w][t] <= hold_prev(v, t)
                for f in F:
                    m += meet_z[v][w][f][t] <= loc[v][f][t]
                    m += meet_z[v][w][f][t] <= loc[w][f][t]
            for t in T:
                m += pulp.lpSum(Q[v][w][t] for w in V3) <= hold_prev(v, t)
        for w in V3:
            for t in T:
                m += pulp.lpSum(Q[v][w][t] for v in V2) <= cap[w] - hold_prev(w, t)

    # Скользящее окно рейса: хотя бы один день в порту.
    for v in V:
        L = vm[v].voyage_limit
        for t0 in T:
            window = [t for t in T if t0 <= t <= t0 + L - 1]
            if len(window) < L:
                continue
            in_port = pulp.lpSum(loc[v][s][t] for s in S for t in window)
            m += in_port >= 1

    # Целевая функция: прибыль = доход - операционные - транспорт - порт - экипаж.
    revenue = pulp.lpSum(
        _unload_price(vm[v], data) * U[v][s][t] for v in carriers for s in S for t in T
    )
    operating = pulp.lpSum(vm[v].daily_fixed_cost for v in V for _t in T)
    operating += pulp.lpSum(
        (data.container_cost[data.product_of_species[g]] + data.production_cost[data.product_of_species[g]])
        * x[v][g][f][t]
        for v in V1
        for g in G
        for f in F
        for t in T
    )
    operating += pulp.lpSum(
        (data.container_cost[p] + data.production_cost[p]) * y[v][p][f][t]
        for v in V2
        for p in data.products
        for f in F
        for t in T
    )
    travel = pulp.lpSum(data.fuel_cost["fishing"] * fish[v][t] for v in V for t in T)
    travel += pulp.lpSum(data.fuel_cost["transit"] * in_tr[v][t] for v in V for t in T)
    port_costs = pulp.lpSum(data.port_entry_cost[s] * entry[v][s][t] for v in V for s in S for t in T)
    port_costs += pulp.lpSum(data.port_idle_cost[s] * idle[v][s][t] for v in V for s in S for t in T)
    port_costs += pulp.lpSum(data.port_repair_cost[s] * repair[v][s][t] for v in V for s in S for t in T)
    crew = pulp.lpSum(vm[v].crew_salary for v in V for _t in T) + data.crew_commission * revenue

    m += revenue - operating - travel - port_costs - crew

    extras = {
        "loc": loc,
        "start": start,
        "in_tr": in_tr,
        "fish": fish,
        "transfer": transfer,
        "repair": repair,
        "idle": idle,
        "unload_bin": unload_bin,
        "meet": meet,
        "x": x,
        "y": y,
        "H": H,
        "U": U,
        "Q": Q,
        "revenue": revenue,
        "operating": operating,
        "travel": travel,
        "port_costs": port_costs,
        "crew": crew,
        "V1": V1,
        "V2": V2,
        "V3": V3,
        "catchers": catchers,
        "carriers": carriers,
    }
    return m, extras


def _unload_price(vessel: Vessel, data: TestInstance) -> float:
    if vessel.kind == "LIVE_CRAB_CARRIER":
        return data.price[data.product_of_species[data.species[0]]]
    return data.price["варено-мороженый краб"]


def solve_model(
    data: TestInstance,
    time_limit: int = 30,
    msg: bool = True,
) -> Tuple[pulp.LpProblem, Dict[str, Any], str]:
    model, extras = build_model(data)
    solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)
    status_code = model.solve(solver)
    status = pulp.LpStatus[status_code]
    return model, extras, status


def extract_schedule(data: TestInstance, extras: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Календарный график в формате раздела 13 документа."""
    loc = extras["loc"]
    start = extras["start"]
    in_tr = extras["in_tr"]
    fish = extras["fish"]
    transfer = extras["transfer"]
    repair = extras["repair"]
    idle = extras["idle"]
    unload_bin = extras["unload_bin"]
    x = extras["x"]
    H = extras["H"]
    U = extras["U"]
    Q = extras["Q"]
    rows: List[Dict[str, Any]] = []

    def val(var: Any) -> float:
        return float(pulp.value(var) or 0.0)

    for vessel in data.vessels:
        v = vessel.id
        for t in data.days:
            route = ""
            status = "Не определено"
            if val(in_tr[v][t]) > 0.5:
                status = "Переход"
                for i, j in data.arcs:
                    for t0 in data.days:
                        dur = data.travel_time[(i, j)]
                        if t0 <= t <= t0 + dur - 1 and val(start[v][i][j][t0]) > 0.5:
                            route = f"{i} -> {j}"
                            break
            else:
                place = next((k for k in data.locations if val(loc[v][k][t]) > 0.5), "")
                route = place
                if any(val(repair[v][s][t]) > 0.5 for s in data.ports):
                    status = "Ремонт"
                elif val(fish[v][t]) > 0.5:
                    status = "Промысел"
                elif val(transfer[v][t]) > 0.5:
                    status = "Перегрузка"
                elif any(val(unload_bin[v][s][t]) > 0.5 for s in data.ports):
                    status = "Порт (отгрузка)"
                elif any(val(idle[v][s][t]) > 0.5 for s in data.ports):
                    status = "Порт (стоянка)"

            catch = 0.0
            if v in extras["catchers"]:
                catch = sum(val(x[v][g][f][t]) for g in data.species for f in data.zones)
            received = 0.0
            if v in extras["V3"]:
                received = sum(val(Q[p][v][t]) for p in extras["V2"])
            unloaded = 0.0
            if v in extras["carriers"]:
                unloaded = sum(val(U[v][s][t]) for s in data.ports)

            rows.append(
                {
                    "Судно": f"{v} ({vessel.name})",
                    "День": t,
                    "Статус": status,
                    "Локация/маршрут": route,
                    "Вылов": round(catch, 3),
                    "Перегрузка": round(received, 3),
                    "Выгрузка": round(unloaded, 3),
                    "Загрузка трюма": round(val(H[v][t]), 3),
                }
            )
    return rows


def objective_breakdown(extras: Dict[str, Any]) -> Dict[str, float]:
    def val(expr: Any) -> float:
        return float(pulp.value(expr) or 0.0)

    revenue = val(extras["revenue"])
    operating = val(extras["operating"])
    travel = val(extras["travel"])
    port_costs = val(extras["port_costs"])
    crew = val(extras["crew"])
    return {
        "Доход": revenue,
        "Операционные затраты": operating,
        "Транспортные затраты": travel,
        "Портовые затраты": port_costs,
        "Оплата экипажу": crew,
        "Прибыль": revenue - operating - travel - port_costs - crew,
    }
