import random
from math import ceil


# Control de Excepciones

class SolucionNoFactible(Exception):
    def __init__(self, msg, datos = None):
        self.message = msg
        self.datos = datos
        super().__init__(self.message)
    def __repr__(self):
        return self.message

class HeuristicaFallida(Exception):
    def __init__(self, msg, paso_de_error = None):
        self.message = msg
        self.paso_de_error = paso_de_error
        super().__init__(self.message)
    def __repr__(self):
        return self.message

def prefijoEnFallidas(hl, fallidas, e):
    for prefijo in fallidas:
        if prefijo != [] and hl[:len(prefijo)] == prefijo:
            return len(prefijo) * e
    else: return 0



# Definicion de las heuristicas constructivas para grafos

def GraphHeuristic(eleccionNodo, grafo, f_opt, n_asignaciones = float('inf')):
    n_it = min( n_asignaciones, len(grafo.nodos_por_color[None]) )
    i = 0
    while i < n_it and len(grafo.nodos_por_color[None]) > 0:
        x = eleccionNodo(grafo)
        valor = float('inf')
        for color in grafo.colores - grafo.nodos[x].colores_vecinos:
            try:
                cambios = grafo.colorear(grafo.nodos[x], color)
                nuevo_val = f_opt(grafo, nodo = x, color = color)
                if nuevo_val < valor:
                    nuevo_color = color
                    valor = nuevo_val
                grafo.revertirCambios(cambios)
            except SolucionNoFactible as e:
                grafo.revertirCambios(e.datos)
                continue
            except Exception as ee:
               print(ee)
               print(type(ee))
               raise ee
        if valor == float('inf'):
            raise HeuristicaFallida("Ningun color disponible es valido", i)
        else:
            a = grafo.colorear(grafo.nodos[x], nuevo_color)
        i += 1


def nodoLargestDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.nodos[x].grado())        

def LargestDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestDegree, grafo, f_obj, n_asignaciones)


def nodoLeastSaturationDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: len(grafo.nodos[x].colores_vecinos))

def LeastSaturationDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLeastSaturationDegree, grafo, f_obj, n_asignaciones)


def nodoLargestColorDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.nodos[x].coloredDegree(grafo))        

def LargestColorDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestColorDegree, grafo, f_obj, n_asignaciones)


def nodoLargestWeightedDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.nodos[x].grado()*grafo.nodos[x].peso())     

def LargestWeightedDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestWeightedDegree, grafo, f_obj, n_asignaciones)
      
    
def nodoLargestEnrollment(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.nodos[x].peso())   

def LargestEnrollment(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestEnrollment, grafo, f_obj, n_asignaciones)


def nodoRandom(grafo):
    return random.choice( list(grafo.nodos_por_color[None]) )

def Random(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoRandom, grafo, f_obj, n_asignaciones)

"""
# Heuristica Propia: Ordena segun el numero de restricciones extra, y en caso de empate segun largest enrolment
def nodoRestriccionesExtra(grafo):
    # Habria que añadir los de exclusion a los datos del grafo y revisar nombres de exclusive y exclusion y exclusivos y tal
    for x, nodo in grafo.nodos_por_color[None].items():
        n_restricciones = 0
        if x in grafo.coincidence.keys(): n_restricciones += len(grafo.coincidence[x])
        if x in grafo.after.keys(): n_restricciones += len(grafo.after[x])
        if x in grafo.before.keys(): n_restricciones += len(grafo.before[x])
        if x in grafo.exclusion.keys(): n_restricciones += len(grafo.exclusion[x])
        if x in grafo.exclusivos.keys(): n_restricciones += len(grafo.exclusivos[x])
    return max(grafo.nodos_por_color[None], key=lambda x: (n_restricciones, grafo.nodos[x].peso()))   

def RestriccionesExtra(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoRestriccionesExtra, grafo, f_obj, n_asignaciones)
"""

# Definicion de los movimientos
    

# El unico movimiento que consideran los autores originales es este para m = 2
def cambiarVarios(x, h, m = 2, *args):
    n = len(x)
    y = x[:]
    l = random.sample(range(n),m)
    for i in l: y[i] = random.choice(h)
    return [y]

def swap(x, h, *args):
    n = len(x)
    y = x[:]
    i, j = random.sample(range(n),2)
    y[i], y[j] = y[j], y[i]
    return [y]

def repetirMov(f, x, h, m = 2, repeticiones = 2):
    y = []
    for l in range(repeticiones):
        y.extend( f(x, h, m) )
    return y


# Definicion de la Graph-HiperHeuristic (GHH)

class GHH():
    def __init__(self, grafo, heuristicas, movimientos, f_obj, f_heur = None, e = 2, tenencia = 9, hl_inicial = None):
        self.grafo = grafo
        self.f_obj = f_obj
        self.f_heur = f_obj if f_heur is None else f_heur
        self.heuristicas = heuristicas
        self.movimientos = movimientos
        self.e = e
        self.n = ceil(len(grafo.nodos_por_color[None])/e)
        self.tenencia = tenencia
        
        # Si no recibe ninguna lista inicial, generamos una aleatoria
        self.hl_actual = [random.choice(heuristicas) for _ in range(self.n)] if hl_inicial is None else hl_inicial
        self.mejor_h = self.hl_actual
        
        self.tabu = [self.hl_actual]
        self.fallidas = []
        try:
            self.mejor_sol = self.aplicar_hl(self.hl_actual)
            self.mejor_val = self.f_obj(self.mejor_sol)
        except Exception as e:
            self.mejor_sol = "Solucion inicial infactible"
            self.mejor_val = float('inf')
            # raise e
    
    def __repr__(self):
        return f"{self.mejor_sol}\n\nCon valor: {self.mejor_val}"
    
    def aplicar_hl(self, hl):
        g = self.grafo.copy()
        for i, h in enumerate(hl):
            try:
                h(g, self.f_heur, self.e)
            except HeuristicaFallida as error:
                self.fallidas.append(hl[:i+1])
                print(i*self.e+error.paso_de_error)
                raise HeuristicaFallida(error.message, i*self.e+error.paso_de_error) from error
                # Medimos la distancia a la factibilidad en funcion del numero de pasos que tarde la heuristica en no encontrar una solucion factible con el objetivo de alcanzar la factibilidad en vecindarios donde todas las soluciones generen coloraciones infactibles
        return g
    
    def generarVecindario(self):
        V = []
        for movimiento in self.movimientos:
            V.extend(movimiento(self.hl_actual, self.heuristicas))
        return V

    def seleccion(self, vecindario):
        prox_hl = self.hl_actual
        prox_g = None
        val_prox_hl = float('inf')
        dist_fact = []
        for hl in vecindario:
            try:
                fallo = prefijoEnFallidas(hl, self.fallidas, self.e)
                if  fallo > 0: 
                    dist_fact.append(fallo)
                    continue
                    # Evitamos volver a ejecutar heurísticas que fallan en un sitio conocido como es sugerido por Burke et al.
                g = self.aplicar_hl(hl)
                val = self.f_obj(g)
                dist_fact.append(0)
                if not(hl in self.tabu) or val < self.mejor_val:        # Aplicamos lista tabu y criterio de aspiracion
                    if val < val_prox_hl:
                        prox_hl = hl
                        prox_g = g
                        val_prox_hl = val
            except HeuristicaFallida as error:
                dist_fact.append(error.paso_de_error)
                continue
        if val_prox_hl == float('inf') :
            # No se ha alcanzado factibilidad en ninguna solucion, tomamos la que mas pasos haya tardado en encontrar infactibilidad, que sera la que mas cerca este de encontrar una solucion factible
            i = max(range(len(vecindario)), key = lambda x : dist_fact[x])
            prox_hl = vecindario[i]
        return prox_hl, prox_g, val_prox_hl


    def iteracion(self):
        vecindario = self.generarVecindario()
        hl, g, val = self.seleccion(vecindario)
        self.hl_actual = hl
        if val < self.mejor_val:
            self.mejor_h = self.hl_actual
            self.mejor_sol = g
            self.mejor_val = val
        if len(self.tabu) >= self.tenencia: self.tabu.pop(0)
        self.tabu.append(hl)            

    def iterar(self, max_it = None):
        if max_it is None: max_it = 10*len(self.grafo.nodos_por_color[None])
        for i in range(max_it):
            self.iteracion()
            print(i, self.mejor_val)





















