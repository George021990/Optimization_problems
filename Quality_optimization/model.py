"""
Модель оптимизации качества продукции на основе лидер-последовательной
(биуровневой) задачи с применением пакета PAO (Pyomo Automation Objects).

Решаемая задача: найти такой уровень качества Q(x, y, z, t), который
минимизирует целевую функцию верхнего уровня при условии, что подчинённые
функциональные подсистемы (управление поставщиками, затраты на качество и
технологичность) в свою очередь оптимально реагируют на выбор переменной x.

Целевые функции нижнего уровня:
    F1(x, y) -> min  — функция управления поставщиками (переменная y);
    F2(x, z) -> min  — функция затрат на качество (переменная z);
    F3(x, t) -> min  — функция технологичности (переменная t).

Задача решается алгоритмом релаксации FA (fixed-point / фиксированной точки)
из модуля pao.pyomo. Все переменные неотрицательны и непрерывны.

Входные данные задаются пользователем с клавиатуры: количество активных
блоков и матрицы показателей качества для компонентов изделия, поставщиков,
категорий затрат на качество и технологических операций. Матрицы
автоматически нормализуются: признаки, у которых отношение суммы показателей
к числу активных позиций меньше 1, считаются «стимулирующими» и меняют знак
коэффициентов в ограничениях на противоположный.
"""
from pyomo.environ import *
from pao.pyomo import *
import numpy as np
# Quality function model with variables x----------------------------------------------------------------------------------
M = ConcreteModel()
M.x = Var(bounds=(0, None), domain=Reals)
# Provider management function model with variables y ----------------------------------------------------------------------------------
M.L = SubModel(fixed=M.x)
M.L.y = Var(bounds=(0, None), domain=Reals) 
# Model of the function "Quality Costs" with variables z ------------------------------------------------------------------------
M.L1 = SubModel(fixed=M.x)
M.L1.z = Var(bounds=(0, None), domain=Reals)
# Manufacturability function model with variables t ------------------------------------------------------------------------
M.L2 = SubModel(fixed=M.x)
M.L2.t = Var(bounds=(0, None), domain=Reals)

# Input information for the quality function -------------------------------------------------------------------------------------------------
N1 = 8 # Number of quality indicators
N2 = 15 # Number of components in the product
A = np.ones((N2,N1)) # Moving from the matrix to the list
N3 = int(input('Please enter number of active blocks')) # Number of active blocks
A[N3:15]=0
MN = list(A) # Quality metrics matrix
for i in range(N3): # Condition for transition from the matrix to the list
    MN[i] = [float(i) for i in input('Please enter numerical values for each quality indicator for components in the product').split()]
MM=np.array(MN)
# Input information for the "Manage Suppliers" function ---------------------------------------------------------------------------------
N11 = 3 # Number of quality indicators
N21 = 20 # Number of suppliers
A11 = np.ones((N21,N11)) # Moving from the matrix to the list
N31 = int(input('Please enter number of active blocks')) # Number of active blocks
A11[N31:20]=0
MN1 = list(A11) # Quality metrics matrix
for i in range(N31): # Condition for transition from the matrix to the list
    MN1[i] = [float(i) for i in input('Please enter numerical values for each quality indicator for each supplier ').split()]
MM1=np.array(MN1)
# Input information for the function "Cost of quality" -----------------------------------------------------------------------
N12 = 3 # Number of quality indicators
N22 = 6 # Quality cost categories
A12 = np.ones((N22,N12)) # Moving from the matrix to the list
N32 = int(input('Please enter number of active blocks')) # Number of active blocks
A12[N32:6]=0
MN2 = list(A12) # Quality metrics matrix
for i in range(N32): # Condition for transition from the matrix to the list
    MN2[i] = [float(i) for i in input('Please enter numerical values for each quality indicator for quality cost categories ').split()]
MM2=np.array(MN2)
# Input information for manufacturability function -----------------------------------------------------------------------
N13 = 4 # Number of quality indicators
N23 = 20 # Number of technological operations
A13 = np.ones((N23,N13)) # Moving from the matrix to the list
N33 = int(input('Please enter number of active blocks')) # Number of active blocks
A13[N33:20]=0
MN3 = list(A13) # Quality metrics matrix
for i in range(N33): # Condition for transition from the matrix to the list
    MN3[i] = [float(i) for i in input('Please enter numerical values for each quality indicator for number of technological operations ').split()]
MM3=np.array(MN3)
# Constraint Conditions for the Quality Function--------------------------------------------------------------------------------------------------
MM=np.array(MN)
n = []
for i in range(len(MM)):
    if len(MM[i])==(sum(MM[i])):
        n.append(sum(MM[i]))
    elif sum(MM[i])==1:
        n.append(sum(MM[i]))
    else:
        n.append(sum(MM[i]))
m=np.array(MM)
for i in range(len(m)):
    for j in range(len(m[i])):
        if m[i,j]==1 or m[i,j]>=1 or m[i,j]>0:
            m[i,j]=1
        else:
            m[i,j]=0
N = []
for i in range(len(m)):
    if len(m[i])==(sum(m[i])):
        N.append(sum(m[i]))
    elif sum(MM[i])==1:
        N.append(sum(m[i]))
    else:
        N.append(sum(m[i]))
c1=np.array(n)
c2=np.array(N)
C=[]
for i in range(len(c1)):
    if c1[i]>0 and c2[i]>0:
        C.append(c1[i]/c2[i])
    else:
        C.append(0)
for i in range(len(m)):
    if 0<C[i]<1:
        MM[i]=MM[i]*-1
        C[i]=C[i]*-1
    else:
        MM[i]=MM[i]
        C[i]=C[i]
# Restriction Conditions for Manage Vendors--------------------------------------------------------------------------------------
MM1=np.array(MN1)
n1 = []
for i in range(len(MM1)):
    if len(MM1[i])==(sum(MM1[i])):
        n1.append(sum(MM1[i]))
    elif sum(MM1[i])==1:
        n1.append(sum(MM1[i]))
    else:
        n1.append(sum(MM1[i]))
m1=np.array(MM1)
for i in range(len(m1)):
    for j in range(len(m1[i])):
        if m1[i,j]==1 or m1[i,j]>=1 or m1[i,j]>0:
            m1[i,j]=1
        else:
            m1[i,j]=0
N1 = []
for i in range(len(m1)):
    if len(m1[i])==(sum(m1[i])):
        N1.append(sum(m1[i]))
    elif sum(MM1[i])==1:
        N1.append(sum(m1[i]))
    else:
        N1.append(sum(m1[i]))
c11=np.array(n1)
c21=np.array(N1)
C1=[]
for i in range(len(c11)):
    if c11[i]>0 and c21[i]>0:
        C1.append(c11[i]/c21[i])
    else:
        C1.append(0)
for i in range(len(m1)):
    if 0<C1[i]<1:
        MM1[i]=MM1[i]*-1
        C1[i]=C1[i]*-1
    else:
        MM1[i]=MM1[i]
        C1[i]=C1[i]
# Constraint Conditions for Quality Cost---------------------------------------------------------------------        
MM2=np.array(MN2)
n2 = []
for i in range(len(MM2)):
    if len(MM2[i])==(sum(MM2[i])):
        n2.append(sum(MM2[i]))
    elif sum(MM2[i])==1:
        n2.append(sum(MM2[i]))
    else:
        n2.append(sum(MM2[i]))
m2=np.array(MM2)
for i in range(len(m2)):
    for j in range(len(m2[i])):
        if m2[i,j]==1 or m2[i,j]>=1 or m2[i,j]>0:
            m2[i,j]=1
        else:
            m2[i,j]=0
N2 = []
for i in range(len(m2)):
    if len(m2[i])==(sum(m2[i])):
        N2.append(sum(m2[i]))
    elif sum(MM2[i])==1:
        N2.append(sum(m2[i]))
    else:
        N2.append(sum(m2[i]))
c12=np.array(n2)
c22=np.array(N2)
C2=[]
for i in range(len(c12)):
    if c12[i]>0 and c22[i]>0:
        C2.append(c12[i]/c22[i])
    else:
        C2.append(0)
for i in range(len(m2)):
    if 0<C2[i]<1:
        MM2[i]=MM2[i]*-1
        C2[i]=C2[i]*-1
    else:
        MM2[i]=MM2[i]
        C2[i]=C2[i]
# Constraint Conditions for the Manufacturability Function -----------------------------------------------------------------------
MM3=np.array(MN3)
n3 = []
for i in range(len(MM3)):
    if len(MM3[i])==(sum(MM3[i])):
        n3.append(sum(MM3[i]))
    elif sum(MM3[i])==1:
        n3.append(sum(MM3[i]))
    else:
        n3.append(sum(MM3[i]))
m3=np.array(MM3)
for i in range(len(m3)):
    for j in range(len(m3[i])):
        if m3[i,j]==1 or m3[i,j]>=1 or m3[i,j]>0:
            m3[i,j]=1
        else:
            m3[i,j]=0
N3 = []
for i in range(len(m3)):
    if len(m3[i])==(sum(m3[i])):
        N3.append(sum(m3[i]))
    elif sum(MM3[i])==1:
        N3.append(sum(m3[i]))
    else:
        N3.append(sum(m3[i]))
c13=np.array(n3)
c23=np.array(N3)
C3=[]
for i in range(len(c13)):
    if c13[i]>0 and c23[i]>0:
        C3.append(c13[i]/c23[i])
    else:
        C3.append(0)
for i in range(len(m3)):
    if 0<C3[i]<1:
        MM3[i]=MM3[i]*-1
        C3[i]=C3[i]*-1
    else:
        MM3[i]=MM3[i]
        C3[i]=C3[i]

# Objective functions ----------------------------------------------------------------------------------------------------
M.obj = Objective(expr=M.model().x - M.model().L.y - M.model().L.y + M.model().L1.z + M.model().L1.z + M.model().L2.t + M.model().L2.t + M.model().L2.t, sense=minimize)# Objective function Q(x,y,z,t)
M.L.obj = Objective(expr = M.model().x + M.model().L.y + M.model().L.y , sense=minimize) # Objective function F1(x,y)
M.L1.obj = Objective(expr= (1-M.model().x) + M.model().L1.z + M.model().L1.z, sense=minimize) # Objective function F2(x,z)
M.L2.obj = Objective(expr=(1-M.model().x) + (1-M.model().L2.t) + (1-M.model().L2.t) + M.model().L2.t, sense=minimize) # Objective function F3(x,t)
# Constraint system for objective function Q(x,y,z,t) ------------------------------------------------------------------------
M.c1 = Constraint(expr=MM[0,0]*M.model().x - MM[0,1]*M.model().L.y - MM[0,2]*M.model().L.y + MM[0,3]*M.model().L1.z + MM[0,4]*M.model().L1.z + MM[0,5]*M.model().L2.t + MM[0,6]*M.model().L2.t + MM[0,7]*M.model().L2.t <= C[0])
M.c2 = Constraint(expr=MM[1,0]*M.model().x - MM[1,1]*M.model().L.y - MM[1,2]*M.model().L.y + MM[1,3]*M.model().L1.z + MM[1,4]*M.model().L1.z + MM[1,5]*M.model().L2.t + MM[1,6]*M.model().L2.t + MM[1,7]*M.model().L2.t <= C[1])
M.c3 = Constraint(expr=MM[2,0]*M.model().x - MM[2,1]*M.model().L.y - MM[2,2]*M.model().L.y + MM[2,3]*M.model().L1.z + MM[2,4]*M.model().L1.z + MM[2,5]*M.model().L2.t + MM[2,6]*M.model().L2.t + MM[2,7]*M.model().L2.t <= C[2])
M.c4 = Constraint(expr=MM[3,0]*M.model().x - MM[3,1]*M.model().L.y - MM[3,2]*M.model().L.y + MM[3,3]*M.model().L1.z + MM[3,4]*M.model().L1.z + MM[3,5]*M.model().L2.t + MM[3,6]*M.model().L2.t + MM[3,7]*M.model().L2.t <= C[3])
M.c5 = Constraint(expr=MM[4,0]*M.model().x - MM[4,1]*M.model().L.y - MM[4,2]*M.model().L.y + MM[4,3]*M.model().L1.z + MM[4,4]*M.model().L1.z + MM[4,5]*M.model().L2.t + MM[4,6]*M.model().L2.t + MM[4,7]*M.model().L2.t <= C[4])
M.c6 = Constraint(expr=MM[5,0]*M.model().x - MM[5,1]*M.model().L.y - MM[5,2]*M.model().L.y + MM[5,3]*M.model().L1.z + MM[5,4]*M.model().L1.z + MM[5,5]*M.model().L2.t + MM[5,6]*M.model().L2.t + MM[5,7]*M.model().L2.t <= C[5])
M.c7 = Constraint(expr=MM[6,0]*M.model().x - MM[6,1]*M.model().L.y - MM[6,2]*M.model().L.y + MM[6,3]*M.model().L1.z + MM[6,4]*M.model().L1.z + MM[6,5]*M.model().L2.t + MM[6,6]*M.model().L2.t + MM[6,7]*M.model().L2.t <= C[6])
M.c8 = Constraint(expr=MM[7,0]*M.model().x - MM[7,1]*M.model().L.y - MM[7,2]*M.model().L.y + MM[7,3]*M.model().L1.z + MM[7,4]*M.model().L1.z + MM[7,5]*M.model().L2.t + MM[7,6]*M.model().L2.t + MM[7,7]*M.model().L2.t <= C[7])
M.c9 = Constraint(expr=MM[8,0]*M.model().x - MM[8,1]*M.model().L.y - MM[8,2]*M.model().L.y + MM[8,3]*M.model().L1.z + MM[8,4]*M.model().L1.z + MM[8,5]*M.model().L2.t + MM[8,6]*M.model().L2.t + MM[8,7]*M.model().L2.t <= C[8])
M.c10 = Constraint(expr=MM[9,0]*M.model().x - MM[9,1]*M.model().L.y - MM[9,2]*M.model().L.y + MM[9,3]*M.model().L1.z + MM[9,4]*M.model().L1.z + MM[9,5]*M.model().L2.t + MM[9,6]*M.model().L2.t + MM[9,7]*M.model().L2.t <= C[9])
M.c11 = Constraint(expr=MM[10,0]*M.model().x - MM[10,1]*M.model().L.y - MM[10,2]*M.model().L.y + MM[10,3]*M.model().L1.z + MM[10,4]*M.model().L1.z + MM[10,5]*M.model().L2.t + MM[10,6]*M.model().L2.t + MM[10,7]*M.model().L2.t <= C[10])
M.c12 = Constraint(expr=MM[11,0]*M.model().x - MM[11,1]*M.model().L.y - MM[11,2]*M.model().L.y + MM[11,3]*M.model().L1.z + MM[11,4]*M.model().L1.z + MM[11,5]*M.model().L2.t + MM[11,6]*M.model().L2.t + MM[11,7]*M.model().L2.t <= C[11])
M.c13 = Constraint(expr=MM[12,0]*M.model().x - MM[12,1]*M.model().L.y - MM[12,2]*M.model().L.y + MM[12,3]*M.model().L1.z + MM[12,4]*M.model().L1.z + MM[12,5]*M.model().L2.t + MM[12,6]*M.model().L2.t + MM[12,7]*M.model().L2.t <= C[12])
M.c14 = Constraint(expr=MM[13,0]*M.model().x - MM[13,1]*M.model().L.y - MM[13,2]*M.model().L.y + MM[13,3]*M.model().L1.z + MM[13,4]*M.model().L1.z + MM[13,5]*M.model().L2.t + MM[13,6]*M.model().L2.t + MM[13,7]*M.model().L2.t <= C[13])
M.c15 = Constraint(expr=MM[14,0]*M.model().x - MM[14,1]*M.model().L.y - MM[14,2]*M.model().L.y + MM[14,3]*M.model().L1.z + MM[14,4]*M.model().L1.z + MM[14,5]*M.model().L2.t + MM[14,6]*M.model().L2.t + MM[14,7]*M.model().L2.t <= C[14])
# Constraint system for objective function F1(x,y) ------------------------------------------------------------------------
M.L.c1 = Constraint(expr=MM1[0,0]*M.model().x + MM1[0,1]*M.model().L.y + MM1[0,2]*M.model().L.y <= C1[0])
M.L.c2 = Constraint(expr=MM1[1,0]*M.model().x + MM1[1,1]*M.model().L.y + MM1[1,2]*M.model().L.y <= C1[1])
M.L.c3 = Constraint(expr=MM1[2,0]*M.model().x + MM1[2,1]*M.model().L.y + MM1[2,2]*M.model().L.y <= C1[2])
M.L.c4 = Constraint(expr=MM1[3,0]*M.model().x + MM1[3,1]*M.model().L.y + MM1[3,2]*M.model().L.y <= C1[3])
M.L.c5 = Constraint(expr=MM1[4,0]*M.model().x + MM1[4,1]*M.model().L.y + MM1[4,2]*M.model().L.y <= C1[4])
M.L.c6 = Constraint(expr=MM1[5,0]*M.model().x + MM1[5,1]*M.model().L.y + MM1[5,2]*M.model().L.y <= C1[5])
M.L.c7 = Constraint(expr=MM1[6,0]*M.model().x + MM1[6,1]*M.model().L.y + MM1[6,2]*M.model().L.y <= C1[6])
M.L.c8 = Constraint(expr=MM1[7,0]*M.model().x + MM1[7,1]*M.model().L.y + MM1[7,2]*M.model().L.y <= C1[7])
M.L.c9 = Constraint(expr=MM1[8,0]*M.model().x + MM1[8,1]*M.model().L.y + MM1[8,2]*M.model().L.y <= C1[8])
M.L.c10 = Constraint(expr=MM1[9,0]*M.model().x + MM1[9,1]*M.model().L.y + MM1[9,2]*M.model().L.y <= C1[9])
M.L.c11 = Constraint(expr=MM1[10,0]*M.model().x + MM1[10,1]*M.model().L.y + MM1[10,2]*M.model().L.y <= C1[10])
M.L.c12 = Constraint(expr=MM1[11,0]*M.model().x + MM1[11,1]*M.model().L.y + MM1[11,2]*M.model().L.y <= C1[11])
M.L.c13 = Constraint(expr=MM1[12,0]*M.model().x + MM1[12,1]*M.model().L.y + MM1[12,2]*M.model().L.y <= C1[12])
M.L.c14 = Constraint(expr=MM1[13,0]*M.model().x + MM1[13,1]*M.model().L.y + MM1[13,2]*M.model().L.y <= C1[13])
M.L.c15 = Constraint(expr=MM1[14,0]*M.model().x + MM1[14,1]*M.model().L.y + MM1[14,2]*M.model().L.y <= C1[14])
M.L.c16 = Constraint(expr=MM1[15,0]*M.model().x + MM1[15,1]*M.model().L.y + MM1[15,2]*M.model().L.y <= C1[15])
M.L.c17 = Constraint(expr=MM1[16,0]*M.model().x + MM1[16,1]*M.model().L.y + MM1[16,2]*M.model().L.y <= C1[16])
M.L.c18 = Constraint(expr=MM1[17,0]*M.model().x + MM1[17,1]*M.model().L.y + MM1[17,2]*M.model().L.y <= C1[17])
M.L.c19 = Constraint(expr=MM1[18,0]*M.model().x + MM1[18,1]*M.model().L.y + MM1[18,2]*M.model().L.y <= C1[18])
M.L.c20 = Constraint(expr=MM1[19,0]*M.model().x + MM1[19,1]*M.model().L.y + MM1[19,2]*M.model().L.y <= C1[19])
# Constraint system for objective function F2(x,z) ------------------------------------------------------------------------
M.L1.c1 = Constraint(expr=MM2[0,0]*M.model().x + MM2[0,1]*M.model().L1.z + MM2[0,2]*M.model().L1.z <= C2[0])
M.L1.c2 = Constraint(expr=MM2[1,0]*M.model().x + MM2[1,1]*M.model().L1.z + MM2[1,2]*M.model().L1.z <= C2[1])
M.L1.c3 = Constraint(expr=MM2[2,0]*M.model().x + MM2[2,1]*M.model().L1.z + MM2[2,2]*M.model().L1.z <= C2[2])
M.L1.c4 = Constraint(expr=MM2[3,0]*M.model().x + MM2[3,1]*M.model().L1.z + MM2[3,2]*M.model().L1.z <= C2[3])
M.L1.c5 = Constraint(expr=MM2[4,0]*M.model().x + MM2[4,1]*M.model().L1.z + MM2[4,2]*M.model().L1.z <= C2[4])
M.L1.c6 = Constraint(expr=MM2[5,0]*M.model().x + MM2[5,1]*M.model().L1.z + MM2[5,2]*M.model().L1.z <= C2[5])
# Constraint system for objective function F3(x,t) ------------------------------------------------------------------------
M.L2.c1 = Constraint(expr=MM3[0,0]*M.model().x + MM3[0,1]*M.model().L2.t + MM3[0,2]*M.model().L2.t + MM3[0,3]*M.model().L2.t <= C3[0])
M.L2.c2 = Constraint(expr=MM3[1,0]*M.model().x + MM3[1,1]*M.model().L2.t + MM3[1,2]*M.model().L2.t + MM3[1,3]*M.model().L2.t <= C3[1])
M.L2.c3 = Constraint(expr=MM3[2,0]*M.model().x + MM3[2,1]*M.model().L2.t + MM3[2,2]*M.model().L2.t + MM3[2,3]*M.model().L2.t <= C3[2])
M.L2.c4 = Constraint(expr=MM3[3,0]*M.model().x + MM3[3,1]*M.model().L2.t + MM3[3,2]*M.model().L2.t + MM3[3,3]*M.model().L2.t <= C3[3])
M.L2.c5 = Constraint(expr=MM3[4,0]*M.model().x + MM3[4,1]*M.model().L2.t + MM3[4,2]*M.model().L2.t + MM3[4,3]*M.model().L2.t <= C3[4])
M.L2.c6 = Constraint(expr=MM3[5,0]*M.model().x + MM3[5,1]*M.model().L2.t + MM3[5,2]*M.model().L2.t + MM3[5,3]*M.model().L2.t <= C3[5])
M.L2.c7 = Constraint(expr=MM3[6,0]*M.model().x + MM3[6,1]*M.model().L2.t + MM3[6,2]*M.model().L2.t + MM3[6,3]*M.model().L2.t <= C3[6])
M.L2.c8 = Constraint(expr=MM3[7,0]*M.model().x + MM3[7,1]*M.model().L2.t + MM3[7,2]*M.model().L2.t + MM3[7,3]*M.model().L2.t <= C3[7])
M.L2.c9 = Constraint(expr=MM3[8,0]*M.model().x + MM3[8,1]*M.model().L2.t + MM3[8,2]*M.model().L2.t + MM3[8,3]*M.model().L2.t <= C3[8])
M.L2.c10 = Constraint(expr=MM3[9,0]*M.model().x + MM3[9,1]*M.model().L2.t + MM3[9,2]*M.model().L2.t + MM3[9,3]*M.model().L2.t <= C3[9])
M.L2.c11 = Constraint(expr=MM3[10,0]*M.model().x + MM3[10,1]*M.model().L2.t + MM3[10,2]*M.model().L2.t + MM3[10,3]*M.model().L2.t <= C3[10])
M.L2.c12 = Constraint(expr=MM3[11,0]*M.model().x + MM3[11,1]*M.model().L2.t + MM3[11,2]*M.model().L2.t + MM3[11,3]*M.model().L2.t <= C3[11])
M.L2.c13 = Constraint(expr=MM3[12,0]*M.model().x + MM3[12,1]*M.model().L2.t + MM3[12,2]*M.model().L2.t + MM3[12,3]*M.model().L2.t <= C3[12])
M.L2.c14 = Constraint(expr=MM3[13,0]*M.model().x + MM3[13,1]*M.model().L2.t + MM3[13,2]*M.model().L2.t + MM3[13,3]*M.model().L2.t <= C3[13])
M.L2.c15 = Constraint(expr=MM3[14,0]*M.model().x + MM3[14,1]*M.model().L2.t + MM3[14,2]*M.model().L2.t + MM3[14,3]*M.model().L2.t <= C3[14])
M.L2.c16 = Constraint(expr=MM3[15,0]*M.model().x + MM3[15,1]*M.model().L2.t + MM3[15,2]*M.model().L2.t + MM3[15,3]*M.model().L2.t <= C3[15])
M.L2.c17 = Constraint(expr=MM3[16,0]*M.model().x + MM3[16,1]*M.model().L2.t + MM3[16,2]*M.model().L2.t + MM3[16,3]*M.model().L2.t <= C3[16])
M.L2.c18 = Constraint(expr=MM3[17,0]*M.model().x + MM3[17,1]*M.model().L2.t + MM3[17,2]*M.model().L2.t + MM3[17,3]*M.model().L2.t <= C3[17])
M.L2.c19 = Constraint(expr=MM3[18,0]*M.model().x + MM3[18,1]*M.model().L2.t + MM3[18,2]*M.model().L2.t + MM3[18,3]*M.model().L2.t <= C3[18])
M.L2.c20 = Constraint(expr=MM3[19,0]*M.model().x + MM3[19,1]*M.model().L2.t + MM3[19,2]*M.model().L2.t + MM3[19,3]*M.model().L2.t <= C3[19])
# Запуск: python model.py
if __name__ == "__main__":
    # Решение двухуровневой задачи алгоритмом релаксации FA (fixed-point) пакета PAO.
    # Внутренний MIP-решатель — HiGHS (модуль highspy, подключён через appsi_highs
    # из пакета pyomo.contrib.appsi).
    solver = Solver('pao.pyomo.FA')
    results = solver.solve(M, mip_solver='appsi_highs', tee=True)

    # Вывод решения
    print()
    print("=== РЕЗУЛЬТАТЫ РЕШЕНИЯ ===")
    print(f"x (качество продукции)     = {value(M.x):.6f}")
    print(f"y (управление поставщиками)= {value(M.L.y):.6f}")
    print(f"z (затраты на качество)    = {value(M.L1.z):.6f}")
    print(f"t (технологичность)        = {value(M.L2.t):.6f}")
    print(f"Статус решателя:           {results.solver.termination_condition}")

