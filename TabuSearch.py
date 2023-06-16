# Tabu Search

class TabuSearch():
    def __init__(self, problema, f_obj, movimientos, tenencia, sol_inicial = None):
        self.problema = problema
        self.f_obj = f_obj
        self.movimientos = movimientos
        self.tenencia = tenencia
        if sol_inicial is None:
            self.sol_actual = problema.generarSolucion()
        else: self.sol_actual = sol_inicial
        self.tabu = []
        self.mejor_sol = self.sol_actual
        self.mejor_val = self.f_obj(self.problema, self.sol_actual)
    
    def __repr__(self):
        return f"Solucion actual: {self.sol_actual}\nLa mejor solucion encontrada es: {self.mejor_sol} con valor: {self.mejor_val}"
        
    def generarVecindario(self):
        V = []
        for movimiento in self.movimientos:
            V.extend(movimiento(self.sol_actual))
        return V
    
    def seleccion(self, vecindario):
        prox_sol = self.sol_actual
        val_prox_sol = float('inf')
        for candidato in vecindario:
            val = self.f_obj(self.problema, candidato)
            if not(candidato in self.tabu) or val < self.mejor_val:        # Aplicamos lista tabu y criterio de aspiracion
                if val < val_prox_sol:
                    prox_sol = candidato
                    val_prox_sol = val
        return prox_sol, val_prox_sol

    def iteracion(self):
        vecindario = self.generarVecindario()
        sol, val = self.seleccion(vecindario)
        self.sol_actual = sol
        
        if len(self.tabu) >= self.tenencia: self.tabu.pop(0)
        self.tabu.append(sol)

        if val < self.mejor_val:
            self.mejor_sol = sol
            self.mejor_val = val
    
    def iterar(self, max_it):
        for i in range(max_it):
            self.iteracion()

"""
Se pueden presentar diferentes variaciones del algoritmo, ya que puede variar la funcion de seleccion, el criterio
de aspiracion, el uso de la memoria explicita o atributiva o añadir estructuras de memoria adicional, por ejemplo

Aqui se presenta una versión que sirve de base para la metaheurística donde la memoria es explícita de corto plazo
(es decir, se acumulan las soluciones explicitas en la lista tabú), el criterio de aspiracion consiste en mejorar 
la solucion global y la seleccion consiste en escoger al mejor vecino que no este en la lista tabu

El criterio de aspiracion sera mas efectivo cuando la funcion objetivo no sea determinista (funciones con ruido o 
aplicaciones de una heuristica) o cuando la memoria usada en la lista tabu sea atributiva (es decir, que prohiba 
movimientos en lugar de soluciones explicitas)
"""


""" 
# Ejemplo de aplicación:

import random

# Definicion de los movimientos

def cambiar1(x):
    n = len(x)
    y = x[:]
    i = random.choice(range(n))
    y[i] = random.randint(0,1)
    return [y]

def cambiar2(x):
    n = len(x)
    y = x[:]
    i, j = random.sample(range(n),2)
    y[i] = random.randint(0,1)
    y[j] = random.randint(0,1)
    return [y]

def cambiar2_multiple(x, m):
    n = len(x)
    y = []
    for l in range(m):
        y.extend( cambiar2(x) )
    return y

def swap(x):
    n = len(x)
    y = x[:]
    i, j = random.sample(range(n),2)
    y[i], y[j] = y[j], y[i]
    return [y]

mov = [cambiar1, cambiar2, lambda x: cambiar2_multiple(x,5) , swap]


# Definicion del problema

problema = {"peso" : [1, 5, 3, 10, 7, 9, 12, 4],
            "valor": [2, 7, 15, 11, 4, 5, 12, 8],
            "capacidad" : 23,
            "dim" : 8}

# Como la TS esta definida para problemas de minimizacion, tratamos las soluciones factibles como las negativas
# Tratamos de minimizar el peso total si es positiva, y si es factible devolvemos la solucion cambiada de signo
def f(problema, sol):
    n = problema["dim"]
    peso_total = sum([ problema["peso"][i] * sol[i] for i in range(n) ])
    if peso_total > problema["capacidad"]:
        return peso_total
    else:
        valor_total = sum([ problema["valor"][i] * sol[i] for i in range(n) ])
        return -valor_total

# Aplicacion del algoritmo

TS = TabuSearch( problema, f, mov, 10, [random.randint(0,1) for i in range(problema["dim"])] )
TS.iterar(100)
print(f"La mejor solucion encontrada para el problema de la mochila es {TS.mejor_sol}")
print(f"Con valor: {-TS.mejor_val}")
print(f"\nLa solucion optima es: [1,1,1,1,0,0,0,1]")
print(f"Con valor: {43}")

"""