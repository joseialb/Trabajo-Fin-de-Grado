import ParticleSwarmOptimization as pso
import time, random
import numpy as np
from numpy import cos, sin, sqrt, exp, e, pi, floor


class Cromosoma():
    def __init__(self,ga, genes = None):
        self.ga = ga
        if genes is None: self.generarGenes()
        else: self.genes = genes
        self.valores = {}
        self.ranks = {}
        
    def __repr__(self):
        return f"Genes: {self.genes}\nValores: {self.valores}\nRanking: {self.rank}\n"

    def generarGenes(self):
        self.genes = []
        for i in range(3):
            self.genes.append(random.uniform(-1,1))
        self.genes.append(random.randint(5,150))
    
    def mutar(self):
        for i in range(3):
            rng = random.normalvariate(0, 0.5)
            self.genes[i] += rng
        # Para el numero de particulas, la mutacion es con respecto a un natural
        rng = random.randint(-10,10)
        self.genes[3] = max(1, self.genes[3] +rng)
        # La unica limitacion de los parametros es que el numero de particulas sea un natural mayor que 0   
            
    # Para cada cromosoma y cada funcion de entrenamiento, se realiza un PSO con los coeficientes del cromosoma y dicha funcion objetivo 
    def evaluar(self, problema):
        w , cog, soc, n_part = self.genes        
        pso_gen = pso.PSO(problema.limInf, problema.limSup, n_part, problema.f, [w, cog, soc])
        t1 = time.time()
        # Realiza todas las iteraciones que tenga tiempo a realizar
        while time.time() - t1 < self.ga.tiempo_limite:
            pso_gen.iteracion()
        self.valores[problema.nombre] = pso_gen.mejor_valor

   
    
# Modificamos la clase GA para que funcione como una hiperheuristica sobre PSO y sea capaz de realizar evaluacion multiobjetivo
class GA:
    def __init__(self, tam, n_torneo, n_elitismo, probMut, problemas, tiempo): 
        self.dim = 4
        self.tam = tam
        self.n_torneo = n_torneo
        self.n_elitismo = n_elitismo
        self.probMut = probMut
        self.problemas = problemas
        self.tiempo_limite = tiempo
        self.poblacion =[Cromosoma(self) for _ in range(self.tam)]
        self.ranking()
    
    def __repr__(self):
        return f"{sorted(ga.poblacion, key = lambda x: x.rank)}"
    
    def ranking(self):
        matriz_valores = []
        for i, problema in enumerate(self.problemas):
            matriz_valores.append([])
            for j, c in enumerate(self.poblacion):
                # if not problema.nombre in c.valores.keys(): c.evaluar(problema)
                c.evaluar(problema) # Volvemos a reevaluar la solucion para, a cambio de repetir el PSO de las soluciones quese mantienen, reducir la estocasticidad e impedir que una mala solucion perviva por mucho tiempo gracias a haber obtenido un buen resultado inicial al azar, solo añade tiempo*elitismo segundos
                matriz_valores[i].append( (c.valores[problema.nombre] , j) )
            matriz_valores[i].sort()
            # A cada elemento le asignamos su rango. Al estar realizando optimizacion continua se asumira que no hay empates
            for i, tupla in enumerate(matriz_valores[i]):
                self.poblacion[tupla[1]].ranks[problema.nombre] = i+1
                
        # Una vez todos esten asignados, calculamos la media de cada uno y guardamos el mejor
        mejorRank = float('inf')
        for c in self.poblacion:
            c.rank = sum(c.ranks.values())/len(c.ranks)
            if c.rank < mejorRank:
                mejorRank = c.rank
                self.mejor = c
    
    # Seleccion por torneo
    def seleccion(self):
        participantes = random.sample(self.poblacion, self.n_torneo)
        return min(participantes, key = lambda x : x.rank)
    
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
        elitismo = sorted(self.poblacion, key = lambda x : x.rank)
        for i in range(self.n_elitismo):
            nueva_poblacion.append(elitismo[i])
        while len(nueva_poblacion) < self.tam:
            p1 = self.seleccion()
            p2 = self.seleccion()
            hijo = self.recombinacion(p1, p2)
            if random.random() < self.probMut: hijo.mutar()
            nueva_poblacion.append(hijo)
        self.poblacion = nueva_poblacion
        self.ranking()
    
    def evolucionar(self, max_it = 100):
        for i in range(max_it):
            self.evolucion()
    
    
    
    
# Definicion de las funciones que van a ser utilizadas como conjunto de entrenamiento como clase para agrupar todos los datos y poder iniciarlas solo con la dimension

class Problema():
    def __init__(self, nombre, dim, limInf, limSup):
        self.nombre = nombre
        self.dim = dim
        self.limInf = limInf
        self.limSup = limSup
    
    def __repr__(self):
        return f"{self.nombre} (Dimensiones: {self.dim})"
    
    
# Funcion esfera entre [-100,...,-100] y [100,...,100]
class Esfera(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Esfera", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        return np.sum(x ** 2)
    
    
# Funcion de Rosenbrock entre [-100,...,-100] y [100,...,100]
class Rosenbrock(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Rosenbrock", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        s = 0
        for i in range(len(x)-1):
            s += 100 * (x[i+1]-x[i]**2)**2 + (x[i]-1)**2
        return s
        

# Funcion de Griewank entre [-100,...,-100] y [100,...,100]
class Griewank(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Griewank", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        s1,s2 = 0,1
        for i,j in enumerate(x):
            s1 += j**2
            s2 *= cos(j/(sqrt(i+1)))
        return 1 + s1/4000 -s2


# Funcion de Rastrigin entre [-5.12,...,-5.12] y [5.12,...,5.12]
class Rastrigin(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Rastrigin", dim,
                          np.array([-5.12]*dim),
                          np.array([5.12]*dim))
    def f(self, x):
        s = 0
        for i in x:
            s += i**2 +10 -10*cos(2*pi*i)
        return s


# Funcion de Ackley entre [-30,...,-30] y [30,...,30]
class Ackley(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Ackley", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        s1,s2 = 0,0
        for i in x:
            s1 += i**2
            s2 +=  cos(2*pi*i)
        # return max(0, e + 20 - 20*exp(-0.2*sqrt(s1/len(x)))-exp(s2/len(x)))
        return e + 20 - 20*exp(-0.2*sqrt(s1/len(x)))-exp(s2/len(x))
        

# Funcion de Schwefel1-2 entre [-100,...,-100] y [100,...,100]
class Schwefel1_2(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Schwefel1-2", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        s = 0
        si = 0
        for i in x:
            si += i
            s += si**2
        return s


# Funcion de Schwefel2-21 entre [-100,...,-100] y [100,...,100]
class Schwefel2_21(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Schwefel2-21", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        return np.max(np.abs(x))


# Funcion de Schwefel2-22 entre [-10,...,-10] y [10,...,10]
# Intervalos mas acotados para evitar overflow a valores infinitos
class Schwefel2_22(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Schwefel2-22", dim,
                          np.array([-10]*dim),
                          np.array([10]*dim))
    def f(self, x):
        s1 = 0
        s2 = 1
        for i in x:
            s1 += abs(i)
            s2 *= abs(i)
        return s1 +s2


# Funcion de Step entre [-100,...,-100] y [100,...,100]
class Step(Problema):
    def __init__(self, dim):
        Problema.__init__(self, "Schwefel2-21", dim,
                          np.array([-100]*dim),
                          np.array([100]*dim))
    def f(self, x):
        s = 0
        for i in x:
            s+= floor(i +0.5)**2
        return s
        


# Aplicacion de la metaoptimización
if __name__ == "__main__":
    # Definicion del conjunto de entrenamiento
    dim = 10
    t = 0.1
    entrenamiento = [Ackley(dim), Griewank(dim),
                     Rosenbrock(dim), Schwefel1_2(dim),
                     Schwefel2_22(dim), Step(dim)]
      
    for i in range(10):
        # Definicion de la hiperheuristica metaoptimizadora
        ga = GA(50, 3, 3, 0.2, entrenamiento, t)
        ga.evolucionar(50)
        w , cog, soc, n_part = ga.mejor.genes
    
        print(f"Entrenamiento {i+1} completado")
        print(f"Coeficientes {(w, cog, soc)}, Numero de Particulas: {n_part}")
        
        pso1_valores = []
        pso2_valores = []
        pso3_valores = []
        
        for j in range(50):
            problema = Rastrigin(dim)
            pso1 = pso.PSO(problema.limInf, problema.limSup, n_part, problema.f, [w, cog, soc])
            t1 = time.time()
            i1 = 0
            while time.time() - t1 < t:
                pso1.iteracion()
                i1 += 1
            pso1_valores.append((i1, pso1.mejor_valor))
            
            problema = Schwefel2_21(dim)
            pso2 = pso.PSO(problema.limInf, problema.limSup, n_part, problema.f, [w, cog, soc])
            t2 = time.time()
            i2 = 0
            while time.time() - t2 < t:
                pso2.iteracion()
                i2 += 1
            pso2_valores.append((i2, pso2.mejor_valor))
            
            problema = Esfera(dim)
            pso3 = pso.PSO(problema.limInf, problema.limSup, n_part, problema.f, [w, cog, soc])
            t3 = time.time()
            i3 = 0
            while time.time() - t3 < t:
                pso3.iteracion()
                i3 += 1
            pso3_valores.append((i3, pso3.mejor_valor))
        
        
        media_i1 = sum( [x[0] for x in pso1_valores] )/50
        media_i2 = sum( [x[0] for x in pso2_valores] )/50
        media_i3 = sum( [x[0] for x in pso3_valores] )/50
        media_pso1 = sum( [x[1] for x in pso1_valores] )/50
        media_pso2 = sum( [x[1] for x in pso2_valores] )/50       
        media_pso3 = sum( [x[1] for x in pso3_valores] )/50       

         
        with open("Coeficientes.txt", "a") as f:
            f.write(f"{dim} & {n_part} & {w:.4f} & {cog:.4f} & {soc:.4f} & ({media_i1}, {media_pso1:.4f}) & ({media_i2}, {media_pso2:.4f}) & ({media_i3}, {media_pso3:.4f})\\\\\n")
        
    
                
                
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            