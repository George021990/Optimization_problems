"""
Автоматический тест модели оптимизации качества (model.py).

Подставляет моделируемые (сгенерированные) входные данные вместо ручного
ввода с клавиатуры, запускает модель и выводит полученное решение.

Схема данных (все показатели приводятся к масштабу 0..3, первая строка —
«эталонная», чтобы у модели были допустимые решения):
  1) Качество продукции: N2=15 компонентов, N1=8 показателей, активных N3=10;
  2) Поставщики:         N21=20, N11=3 показателя, активных N31=14;
  3) Затраты на качество:N22=6,  N12=3 показателя, активных N32=4;
  4) Технологичность:    N23=20, N13=4 показателя, активных N33=12.
"""
import builtins
import math
import random

import numpy as np
from pyomo.environ import value

random.seed(2026)

# --- Генерация строк входных данных -----------------------------------------
values = []


def add_block(n_rows, n_cols, active, lo=0.0, hi=3.0):
    """Добавляет блок ввода: число активных блоков + сами строки матрицы."""
    values.append(str(active))
    for i in range(active):
        if i == 0:
            # эталонная строка: все показатели >=1 (не «стимулирующие»)
            row = [1.0 + random.random() * 2.0 for _ in range(n_cols)]
        else:
            row = [1.0 + random.random() * 2.0 for _ in range(n_cols)]
        values.append(" ".join(f"{v:.2f}" for v in row))
    # неактивные строки (нулевые) не вводятся, они и так зануляются в модели


# Блок 1: качество продукции (15 компонентов x 8 показателей, активных 10)
add_block(15, 8, active=10)
# Блок 2: поставщики (20 x 3, активных 14)
add_block(20, 3, active=14)
# Блок 3: затраты на качество (6 x 3, активных 4)
add_block(6, 3, active=4)
# Блок 4: технологичность (20 x 4, активных 12)
add_block(20, 4, active=12)

# --- Подмена input() ----------------------------------------------------------
inputs = iter(values)
real_input = builtins.input


def fake_input(prompt=""):
    try:
        v = next(inputs)
    except StopIteration:
        raise RuntimeError("Входные данные закончились раньше, чем их ожидала модель")
    print(f"[подменённый ввод] {v}")
    return v


builtins.input = fake_input

# --- Запуск модели ------------------------------------------------------------
import model  # повторяет построение модели; input() уже подменён

# --- Диагностика: какие ограничения константны (степень 0) ---------------------
from pyomo.environ import Constraint
print("\nКонстантные ограничения (степень 0):")
for cdata in model.M.component_data_objects(Constraint, active=True):
    if cdata.expr.polynomial_degree() == 0:
        print(f"  {cdata.name}: {cdata.expr} <= {cdata.upper}")

# --- Решение ------------------------------------------------------------------
from pao.pyomo import Solver
solver = Solver("pao.pyomo.FA")
results = solver.solve(model.M, mip_solver="appsi_highs", tee=False)

# --- Печать результатов ---------------------------------------------------------
print("\n=== РЕЗУЛЬТАТЫ РЕШЕНИЯ ===")
print(f"x (качество продукции)              = {value(model.M.x):.6f}")
print(f"y (управление поставщиками)         = {value(model.M.L.y):.6f}")
print(f"z (затраты на качество)             = {value(model.M.L1.z):.6f}")
print(f"t (технологичность)                 = {value(model.M.L2.t):.6f}")
print(f"Q(x,y,z,t) (лидер)                  = {value(model.M.obj):.6f}")
print(f"F1(x,y)   (поставщики)              = {value(model.M.L.obj):.6f}")
print(f"F2(x,z)   (затраты на качество)     = {value(model.M.L1.obj):.6f}")
print(f"F3(x,t)   (технологичность)         = {value(model.M.L2.obj):.6f}")
print(f"Статус решателя: {results.solver.termination_condition}")