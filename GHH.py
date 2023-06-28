import random, time
from math import ceil, exp


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

# Version predictiva, se elige el color que menos añade a la funcion objetivo
def GraphHeuristic(eleccionNodo, grafo, f_pred, n_asignaciones = float('inf')):
    n_it = min( n_asignaciones, len(grafo.nodos_por_color[None]) )
    i = 0
    while i < n_it and len(grafo.nodos_por_color[None]) > 0:
        x = eleccionNodo(grafo)
        valor = float('inf')
        colores_disponibles = list(grafo.colores - grafo.nodos[x].colores_vecinos)
        valores = []
        for color in colores_disponibles:
            valores.append(f_pred(grafo, nodo = x, color = color))
        
        while len(colores_disponibles) > 0:
            try:
                indice = min(range(len(valores)), key = lambda i : valores[i])
                color = colores_disponibles[indice]
                grafo.colorear(grafo.nodos[x], color)
                break
            except SolucionNoFactible as e:
                grafo.revertirCambios(e.datos)
                colores_disponibles.remove(color)
                valores.pop(indice)
        
        if len(colores_disponibles) == 0:
            raise HeuristicaFallida("Ningun color disponible es valido", i)
        i += 1


# Version predictiva con ruleta: Para cada color, predice el incremento de la funcion objetivo que va a generar colorear el nodo x y en base a esto le asigna una probabilidad
# inversa a dicho valor. Posteriormente aplica la selección por ruleta e intenta colorear el nodo de dicho color. Si no es factible, vuelve a seleccionar otro color hasta que no queden
def GraphHeuristicRuleta(eleccionNodo, grafo, f_pred, n_asignaciones = float('inf')):
    n_it = min( n_asignaciones, len(grafo.nodos_por_color[None]) )
    i = 0
    while i < n_it and len(grafo.nodos_por_color[None]) > 0:
        x = eleccionNodo(grafo)
        valor = float('inf')
        colores_disponibles = list(grafo.colores - grafo.nodos[x].colores_vecinos)
        probabilidades = []
        for color in colores_disponibles:
            probabilidades.append(10*exp(-2*f_pred(grafo, nodo = x, color = color)))
        
        while len(colores_disponibles) > 0:
            try:
                limites_ruleta, contador = [] , 0
                for prob in probabilidades:
                    contador += prob
                    limites_ruleta.append(contador)            
                ruleta = random.uniform(0,contador)
                for indice, limite in enumerate(limites_ruleta):
                    if ruleta <= limite:
                        color = colores_disponibles[indice]
                        break
                grafo.colorear(grafo.nodos[x], color)
                break
            except SolucionNoFactible as e:
                grafo.revertirCambios(e.datos)
                colores_disponibles.remove(color)
                probabilidades.pop(indice)
        
        if len(colores_disponibles) == 0:
            raise HeuristicaFallida("Ningun color disponible es valido", i)
        i += 1
        

# Variacion sin prediccion: Para elegir el color del nodo, para cada color disponible, colorea el nodo con dicho color, calcula la funcion de optimizacion f_opt 
# (que puede ser la funcion objetivo o el incremento de esta para mas eficiencia) y revierte los cambios. Elige el color que menor valor de f_opt devuelva
# def ColorGraphHeuristicSinPrediccion(eleccionNodo, grafo, f_opt, n_asignaciones = float('inf')):
#     n_it = min( n_asignaciones, len(grafo.nodos_por_color[None]) )
#     i = 0
#     while i < n_it and len(grafo.nodos_por_color[None]) > 0:
#         x = eleccionNodo(grafo)
#         valor = float('inf')
#         for color in grafo.colores - grafo.nodos[x].colores_vecinos:
#         # for color in random.sample(list(colores_disponibles), len(colores_disponibles)//2):  # Tambien es posible tomar un subconjunto aleatorio para aligerar la busqueda, puede empeorar el resultado pero al ser no determinista, diversifica la búsqueda       
#             try:
#                 cambios = grafo.colorear(grafo.nodos[x], color)
#                 nuevo_val = f_opt(grafo, nodo = x, color = color)
#                 if nuevo_val < valor:
#                     nuevo_color = color
#                     valor = nuevo_val
#                 grafo.revertirCambios(cambios)
#             except SolucionNoFactible as e:
#                 grafo.revertirCambios(e.datos)
#                 continue
#         if valor == float('inf'):
#             raise HeuristicaFallida("Ningun color disponible es valido", i)
#         else:
#             a = grafo.colorear(grafo.nodos[x], nuevo_color)
#         i += 1



def nodoLargestDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.grado(x))        

def LargestDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestDegree, grafo, f_obj, n_asignaciones)


def nodoLeastSaturationDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: len(grafo.nodos[x].colores_vecinos))

def LeastSaturationDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLeastSaturationDegree, grafo, f_obj, n_asignaciones)


def nodoLargestColorDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.gradoColor(x))        

def LargestColorDegree(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoLargestColorDegree, grafo, f_obj, n_asignaciones)


def nodoLargestWeightedDegree(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.grado(x)*grafo.nodos[x].peso())     

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


# Heuristica Propia: Da prioridad a las heuristicas con restricciones extra que son modelizadas durante la coloracion
def nodoGradoRestricciones(grafo):
    return max(grafo.nodos_por_color[None], key=lambda x: grafo.gradoRestricciones(x))

def GradoRestricciones(grafo, f_obj, n_asignaciones = float('inf')):
    return GraphHeuristic(nodoGradoRestricciones, grafo, f_obj, n_asignaciones)



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
    def __init__(self, grafo, heuristicas, movimientos, f_obj, f_pred = None, e = 2, tenencia = 9, hl_inicial = None):
        self.grafo = grafo
        self.f_obj = f_obj
        self.f_pred = f_obj if f_pred is None else f_pred
        self.heuristicas = heuristicas
        self.movimientos = movimientos
        self.e = e
        self.n = ceil(len(grafo.nodos_por_color[None])/e)
        self.tenencia = tenencia
        self.i, self.t = 0,0
        
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
                h(g, self.f_pred, self.e)
            except HeuristicaFallida as error:
                self.fallidas.append(hl[:i+1])
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
                    # Evitamos volver a ejecutar heurísticas que fallan en un sitio conocido, como es sugerido por Burke et al.
                g = self.aplicar_hl(hl)
                val = self.f_obj(g)
                dist_fact.append(0)
                if val < self.mejor_val or not(hl in self.tabu):        # Aplicamos lista tabu y criterio de aspiracion
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
        a = time.time()

        vecindario = self.generarVecindario()
        hl, g, val = self.seleccion(vecindario)
        self.hl_actual = hl
        if val < self.mejor_val:
            self.mejor_h = self.hl_actual
            self.mejor_sol = g
            self.mejor_val = val
        if len(self.tabu) >= self.tenencia: self.tabu.pop(0)
        self.tabu.append(hl)    
        
        self.i += 1
        tiempo_iteracion = time.time() - a
        self.t += tiempo_iteracion
        return tiempo_iteracion

    def iterar(self, max_it = None):
        if max_it is None: max_it = 10*len(self.grafo.nodos_por_color[None])
        for i in range(max_it):
            t = self.iteracion()
            if self.i % 100 == 0: print(f"Iteracion {self.i}. Valor obtenido: {self.mejor_val}, Tiempo de iteracion: {t}")





















