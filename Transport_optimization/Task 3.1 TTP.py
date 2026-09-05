#!/usr/bin/env python
# coding: utf-8

# In[6]:


from pyomo.environ import *
import math
import numpy as np



def TTP(XX):
    H = [15,22] # Доступная вместимость транспорта в кг
    D = XX  # Требование клиента в кг
    P = [10,10] # Транспорт доступный для аренды
    t0 = [12,10,16] # Требуемое время доставки (в днях)
    t11 = [6,15,6] # время доставки транспорта p1 (в днях)
    t12 = [6,6,20] # время доставки транспорта p2 (в днях)
    G = [145,160] # Стоимость перевозки (руб/км) j-го транспорта i-ому клиенту. 
    R = [56, 67, 48] # расстояние от ТК до клиента (км.)
    R01 = [G[0]*x for x in R] # стоимости эксплуатации транспорта типа p1 в зависимости от пройденного пути (от комбината до клиента)
    R02 = [G[1]*x for x in R] # стоимости эксплуатации транспорта типа p2 в зависимости от пройденного пути (от комбината до клиента)


    M = 10000

    model = ConcreteModel()


    # 1 Основные переменные

# Всего доступно 2 типа транспорта (p1,p2)
# 1.1 Количество активного транспорта типа p1 для доставки продукции   
    model.p11 = Var(within=Integers, bounds=(0,10)) # Первый маршрут. Клиент №1
    model.p12 = Var(within=Integers, bounds=(0,10)) # Второй маршрут. Клиент №2
    model.p13 = Var(within=Integers, bounds=(0,10)) # Третий  маршрут. Клиент №3

# 1.2 Количество активного транспорта типа p2 для доставки продукции    

    model.p21 = Var(within=Integers, bounds=(0,10)) # Первый маршрут. Клиент №1
    model.p22 = Var(within=Integers, bounds=(0,10)) # Второй маршрут. Клиент №2
    model.p23 = Var(within=Integers, bounds=(0,10)) # Третий  маршрут. Клиент №3

# 1.3 Стоимость эксплуатации транспорта для доставки продукции 
    model.s11 = Var(bounds=(0, None), domain=Reals) # Первый маршрут. Клиент №1
    model.s12 = Var(bounds=(0, None), domain=Reals) # Второй маршрут. Клиент №2
    model.s13 = Var(bounds=(0, None), domain=Reals) # Третий  маршрут. Клиент №3
    model.s21 = Var(bounds=(0, None), domain=Reals) # Первый маршрут. Клиент №1
    model.s22 = Var(bounds=(0, None), domain=Reals) # Второй маршрут. Клиент №2
    model.s23 = Var(bounds=(0, None), domain=Reals) # Третий  маршрут. Клиент №3


# 2 Дополнительные булевые переменные

    model.x1 = Var(domain=Binary,bounds=(0,1))  
    model.x2 = Var(domain=Binary,bounds=(0,1))
    model.x3 = Var(domain=Binary,bounds=(0,1))

    model.y11 = Var(domain=Binary,bounds=(0,1))  
    model.y12 = Var(domain=Binary,bounds=(0,1))  
    model.y13 = Var(domain=Binary,bounds=(0,1))  
    model.y21 = Var(domain=Binary,bounds=(0,1))  
    model.y22 = Var(domain=Binary,bounds=(0,1))  
    model.y23 = Var(domain=Binary,bounds=(0,1)) 

    model.z1 = Var(domain=Binary,bounds=(0,1))  
    model.z2 = Var(domain=Binary,bounds=(0,1))
    model.z3 = Var(domain=Binary,bounds=(0,1))

    model.z4 = Var(domain=Binary,bounds=(0,1))  
    model.z5 = Var(domain=Binary,bounds=(0,1))
    model.z6 = Var(domain=Binary,bounds=(0,1))


# Целевая функция.
    model.obj = Objective(expr=model.s11+model.s12+model.s13+model.s21+model.s22+model.s23, sense=minimize)

# Требование к грузу (3.1).

    model.B1 = Constraint(expr = H[0]*model.p11+H[1]*model.p21>=D[0]*model.x1)
    model.B2 = Constraint(expr = H[0]*model.p12+H[1]*model.p22>=D[1]*model.x2)
    model.B3 = Constraint(expr = H[0]*model.p13+H[1]*model.p23>=D[2]*model.x3)

    model.B4 = Constraint(expr = model.p11+model.p12+model.p13<=10)
    model.B5 = Constraint(expr = model.p21+model.p22+model.p23<=10)
#------------------------------------------------

    model.B6 = Constraint(expr = model.x1+model.x2+model.x3==3)

# Требование к времени доставки (3.2).

    model.B7 = Constraint(expr = model.p11<=M*(model.y11))
    model.B8 = Constraint(expr = model.p12<=M*(model.y12))
    model.B9 = Constraint(expr = model.p13<=M*(model.y13))

    model.B10 = Constraint(expr = model.p21<=M*(model.y21))
    model.B11 = Constraint(expr = model.p22<=M*(model.y22))
    model.B12 = Constraint(expr = model.p23<=M*(model.y23))

    model.B13 = Constraint(expr = model.y11<=2**(t0[0]-t11[0]))
    model.B14 = Constraint(expr = model.y12<=2**(t0[1]-t11[1]))
    model.B15 = Constraint(expr = model.y13<=2**(t0[2]-t11[2]))

    model.B16 = Constraint(expr = model.y21<=2**(t0[0]-t12[0]))
    model.B17 = Constraint(expr = model.y22<=2**(t0[1]-t12[1]))
    model.B18 = Constraint(expr = model.y23<=2**(t0[2]-t12[2]))

# Требование к стоимости доставки (3.3).

# 3.3.1 Выбор транспорта для маршрута №1
    model.B19 = Constraint(expr = model.s11<=R01[0]*model.p11)
    model.B20 = Constraint(expr = model.s21<=R02[0]*model.p21)
    model.B21 = Constraint(expr = model.s11>=R01[0]*model.p11-M*(1-model.z1))
    model.B22 = Constraint(expr = model.s21>=R02[0]*model.p21-M*(1-model.z2))
    model.B23 = Constraint(expr = model.z1+model.z2 == 1)

# 3.3.2 Выбор транспорта для маршрута №2

    model.B24 = Constraint(expr = model.s12<=R01[1]*model.p12)
    model.B25 = Constraint(expr = model.s22<=R02[1]*model.p22)
    model.B26 = Constraint(expr = model.s12>=R01[1]*model.p12-M*(1-model.z3))
    model.B27 = Constraint(expr = model.s22>=R02[1]*model.p22-M*(1-model.z4))
    model.B28 = Constraint(expr = model.z3+model.z4 == 1)

# 3.3.2 Выбор транспорта для маршрута №3

    model.B29 = Constraint(expr = model.s13<=R01[2]*model.p13)
    model.B30 = Constraint(expr = model.s23<=R02[2]*model.p23)
    model.B31 = Constraint(expr = model.s13>=R01[2]*model.p13-M*(1-model.z5))
    model.B32 = Constraint(expr = model.s23>=R02[2]*model.p23-M*(1-model.z6))
    model.B33 = Constraint(expr = model.z5+model.z6 == 1)

    opt = SolverFactory('glpk')

    results = opt.solve(model)


    print('Целевая функция затрат =', + round(value(model.obj)))
    print('Количество активных машин типа р1 на маршрутах №1-3 =', + round(value(model.p11)), + round(value(model.p12)), + round(value(model.p13)))      
    print('Количество активных машин типа р2 на маршрутах №1-3 =', + round(value(model.p21)), + round(value(model.p22)), + round(value(model.p23)))
    print('Затраты на транспорт р1 =', + round(value(model.s11+model.s12+model.s13)))
    print('Затраты на транспорт р2 =', + round(value(model.s21+model.s22+model.s23)))

