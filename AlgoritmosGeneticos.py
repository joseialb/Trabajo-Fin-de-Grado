import random
import numpy as np


class GA:
    def __init__(self, tam, n_torneo, n_elitismo, probMut, limInf, limSup, f): 
        self.LI = limInf
        self.LS = limSup
        self.dim = len(limInf)
        self.tam = tam
        self.n_torneo = n_torneo
        self.n_elitismo = n_elitismo
        self.probMut = probMut
        self.f = f        
        self.mejorVal = float('inf')
        self.poblacion =[Cromosoma(self) for _ in range(self.tam)]
        for c in self.poblacion: c.evaluar()

    
    def __repr__(self):
        return f"{self.mejor}, {self.mejorVal}"
            
    # Seleccion por torneo
    def seleccion(self):
        participantes = random.sample(self.poblacion, self.n_torneo)
        return min(participantes, key = lambda x : x.valor)
    
    # Recombinacion Uniforme
    def recombinacion(self, p1, p2):
        hijo = []
        for i in range(self.dim):
            if random.random() < 0.5:
                hijo.append(p1.genes[i])
            else:
                hijo.append(p2.genes[i])
        return Cromosoma(self, hijo)
    
    def evolucion(self):
        nueva_poblacion = []
        elitismo = sorted(self.poblacion, key = lambda x : x.valor)
        for i in range(self.n_elitismo):
            nueva_poblacion.append(elitismo[i])
        while len(nueva_poblacion) < self.tam:
            p1 = self.seleccion()
            p2 = self.seleccion()
            hijo = self.recombinacion(p1, p2)
            if random.random() < self.probMut: hijo.mutar()
            hijo.evaluar()
            nueva_poblacion.append(hijo)
        self.poblacion = nueva_poblacion
    
    def evolucionar(self, max_it = 100):
        for i in range(max_it):
            self.evolucion()


    
class Cromosoma():
    def __init__(self,ga, genes = None):
        self.ga = ga
        self.genes = np.random.uniform(ga.LI, ga.LS) if genes is None else genes

    def __repr__(self):
        return f"Genes: {self.genes}\n Valor: {self.valor}"
    
    def mutar(self):
        for i in range(self.ga.dim):
            rng = random.normalvariate(0, 0.5)
            self.genes[i] += rng
            
    def evaluar(self):
        self.valor = self.ga.f(self.genes)    
        if self.valor < self.ga.mejorVal:
            self.ga.mejorVal = self.valor
            self.ga.mejor = self.genes[:]
    

        
    
# Funciones de testing

# Esfera
def f1(x):
    return sum([x[i] ** 2 for i in range(len(x))])

LU = [100 for i in range(3)]
LI = [-100 for i in range(3)]





ga1 = GA(100, 4, 5, 0.2, LI, LU, f1) 
ga1.evolucionar(10000)
print(ga1)
    