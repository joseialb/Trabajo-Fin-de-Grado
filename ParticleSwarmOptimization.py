import numpy
import random

# Vecindario Total
class PSO():
    def __init__(self, limInf, limSup, n_part, f, coef, vecindarios = None):
        self.f = f
        self.limInf = limInf
        self.limSup = limSup
        self.dim = len(limInf)
        self.tam = n_part
        self.vecindarios = vecindarios
        self.particulas = [Particula(i, self) for i in range(self.tam)]
        self.inercia, self.cognitivo, self.social = coef
        self.mejor_valor = float('inf')
        for p in self.particulas:
            if p.mejor_valor < self.mejor_valor :
                self.mejor_particula = p
                self.mejor_posicion = p.mejor_posicion
                self.mejor_valor = p.mejor_valor
                
    def __repr__(self):
        return f"Mejor Particula:\n{self.mejor_particula}\nValor:\n{self.mejor_valor}"
    
    def mostrarTodas(self):
        salida = ""
        for i,p in enumerate(self.part):
            salida += f"Particula {i}:\n{p}\n\n"
        return salida
    
    def iteracion(self):
        # Síncrono
        for i in range(self.tam):
            self.particulas[i].mover()
        for i in range(self.tam):    
            self.particulas[i].actualizar_vel(self.inercia, self.cognitivo, self.social)
        # Asíncrono
        # for i in range(self.tam):
        #     self.part[i].mover()
        #     self.part[i].actualizar_vel(self.inercia, self.cognitivo, self.social)
            
    def iterar(self, n = 100):
        for _ in range(n):
            self.iteracion()
    

class Particula():
    def __init__(self, p_id, pso, **kargs):        
        self.id = p_id
        self.pso = pso
        self.pos = kargs.get("posicion", numpy.random.uniform(pso.limInf, pso.limSup))
        self.vel = kargs.get("velocidad", 0.5 * numpy.random.uniform(pso.limInf - self.pos, pso.limSup - self.pos))
        self.vec = kargs.get("vecindario", None if self.pso.vecindarios is None else self.pso.vecindarios[p_id]) 
        self.mejor_posicion = self.pos[:]
        self.mejor_valor = self.pso.f(self.pos)
        
    def __repr__(self):
        salida =  f"Posicion actual: {self.pos}"
        salida += f"\nVelocidad actual: {self.vel}"
        salida += f"\nMejor posicion: {self.mejor_posicion}"
        salida += f"\nValor de la mejor posicion: {self.mejor_valor}"
        return salida
                    
    def mover(self):
        self.pos += self.vel
        self.pos = numpy.clip(self.pos, self.pso.limInf, self.pso.limSup)
        aux = self.pso.f(self.pos)
        if aux < self.mejor_valor:
            self.mejor_posicion = self.pos.copy()
            self.mejor_valor = aux
        if aux < self.pso.mejor_valor:
            self.pso.mejor_posicion = self.mejor_posicion
            self.pso.mejor_valor = aux
        
    def actualizar_vel(self,w,cog,soc):
        n = self.pso.dim
        if self.vec is None: 
            v1 , v2 = self.mejor_posicion - self.pos , self.pso.mejor_posicion - self.pos
        else: 
            for p2 in self.vec:
                if p2.mejor_valor < self.mejor_valor_vecina:
                    self.mejor_posicion_vecina = p2.mejor_posicion
                    self.mejor_valor_vecina = p2.mejor_valor
            v1 , v2 = self.mejor_posicion - self.pos , self.mejor_posicion_vecina - self.pos
        self.vel = w*self.vel + cog*numpy.random.random(n)*v1 + soc*numpy.random.random(n)*v2    

"""
Aqui s epresenta la implementacion de Particle Swarm Optimization. 
Existen distintas variaciones, la aqui presentada consiste en la síncrona, pero puede darse también asíncrona
o incluso variaciones discretas del algoritmo

Si el vecindario es el conjunto total de particulas, el coste de cada iteracion es lineal, ya que se usa el 
mejor valor global. En caso de tener vecindarios de tamaño k, el coste por iteracion será O(k*n_part)
"""


""" 
# Ejemplo de aplicación:

from numpy import cos, sqrt, exp, e, pi

# Definicion de la función objetivo

# Función de Rastrigin 
def Rastrigin(x):
    s = 0
    for i in x:
        s += i**2 +10 -10*cos(2*pi*i)
    return s

# Esta funcion tiene un minimo absoluto en x = [0,0,...,0] con valor 0


# Definicion del espacio de búsqueda

dim = 5
limInf = np.array([-5.12] * dim)
limSup = np.array([5] * dim)


# Definicion de la metaheuristica:
n_part = 100
coef = [0.2 , 0.7, 0.7]
p = PSO(limInf, limSup, n_part, Rastrigin, coef)

p.iterar(100)

"""





        