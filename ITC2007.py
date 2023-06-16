import numpy as np
import random
from GHH import SolucionNoFactible
import GHH
from math import ceil
"""
Formato de datos de ITC 2007
"""

        
# Estructuras de datos para grafos

class Nodo():
    def __init__(self, n_id, tipo, objeto, color = None, adyacentes = None):
        self.id = n_id
        self.tipo = tipo
        self.objeto = objeto
        self.color = color
        self.adyacentes = set() if adyacentes is None else adyacentes
    
    def __repr__(self):
        return f"{self.id}: {self.color}"
    
    def copy(self):
        return Nodo(self.id, self.tipo, self.objeto, self.color, self.adyacentes.copy())
    
    def grado(self):
        return len(self.adyacentes)
    
    def coloredDegree(self, grafo):
        s = 0
        for id2 in self.adyacentes:
            if grafo.nodos[id2].color is not None: s+=1
        return s
    
    def peso(self):
        try:
            s = self.objeto.size
        except:
            s = 1
        return s
    
            
class Grafo():
    def __init__(self, colores = set(), before = {}, after = {}, coincidence = {}):
        self.nodos = {}      
        self.colores = set() if colores is None else colores
        self.nodos_por_color = {None : set()}
        for color in colores:
            self.nodos_por_color[color] = set()
        
        self.before = {} if before is None else before
        self.after = {} if after is None else after
        self.coincidence = {} if coincidence is None else coincidence 
        
    def __repr__(self):
        s = "Nodos\n\n"
        for nodo in self.nodos.values():
            s+= f"{nodo}\n"
        s += "\n\nAristas:\n\n"
        for arista in self.aristas():
            s += f"{arista}\n"
        return s
    
    def __eq__(self, grafo):
        return self.nodos_por_color == grafo.nodos_por_color
    
    def aristas(self):
        a = set()
        for nodo in self.nodos.values():
            for nodo2 in nodo.adyacentes:
                a.add( (nodo.id, nodo2) )
        return a
    
    def add_nodo(self, nodo):
        self.nodos[nodo.id] = nodo
        self.nodos_por_color[nodo.color].add(nodo.id)
        
    def colores_vecinos(self, nodo_id):
        return ( {self.nodos[id2].color for id2 in self.nodos[nodo_id].adyacentes} - {None} )
    
    def colorear(self, nodo, color):
        if nodo.color != color:
            color_anterior = nodo.color
            if color is None: nodo.color = color
            elif not(color in self.colores_vecinos(nodo.id)):
                nodo.color = color
                # Comprobamos que no se pierda factibilidad
                for id2 in nodo.adyacentes:
                    if self.nodos[id2].color is None and len(self.colores_vecinos(id2)) >= len(self.colores):
                        raise SolucionNoFactible("El color indicado deja sin posibles colores a un nodo adyacente")
            else:
                raise SolucionNoFactible("El color indicado coincide con el color de un nodo adyacente")
            self.nodos_por_color[color_anterior].remove(nodo.id)
            self.nodos_por_color[color].add(nodo.id)
    
    # Descolorear con None no es recomendable por que no se sabe como afectaría a las posibles aristas que hayan sido añadidas al colorear
    def colorear_con_restricciones(self, nodo, color):
        if nodo.color != color:        
            self.colorear(nodo, color)
            # Mantenemos las restricciones de Coincidence y After de forma dinamica
            if nodo.id in self.before.keys():
                for id2 in self.before[nodo.id]:
                    if self.nodos[id2].color is not None: continue
                    for i in filter(lambda x : x < color, self.colores):
                        self.add_arista(self.nodos[id2], self.nodos[("color", i)] )
                    if len(self.colores_vecinos(id2)) >= len(self.colores):
                        raise SolucionNoFactible("El color indicado deja sin posibles colores a un nodo que debe asignarse en un horario anterior")
            
            if nodo.id in self.after.keys():
                for id2 in self.after[nodo.id]:
                    if self.nodos[id2].color is not None: continue
                    for i in filter(lambda x : x > color, self.colores):
                        self.add_arista(self.nodos[id2], self.nodos[("color", i)] )
                    if len(self.colores_vecinos(id2)) >= len(self.colores):
                        raise SolucionNoFactible("El color indicado deja sin posibles colores a un nodo que debe asignarse en un horario posterior")     
            
            if nodo.id in self.coincidence.keys():
                for id2 in self.coincidence[nodo.id]:
                    self.colorear_con_restricciones(self.nodos[id2], color)
    
    def nodos_cambiados(self, nodo, color, s = None):
        if s is None: s = {}
        if not nodo in s.keys():
            s[nodo] = self.nodos[nodo].copy()
            if nodo in self.before.keys():
                for nodo2 in self.before[nodo]: s[nodo2] = self.nodos[nodo2].copy()
                # for i in filter(lambda x : x < color, self.colores): s[("color", i)] = self.nodos[("color", i)].copy()
            if nodo in self.after.keys():
                for nodo2 in self.after[nodo]: s[nodo2] = self.nodos[nodo2].copy()
                # for i in filter(lambda x : x > color, self.colores): s[("color", i)] = self.nodos[("color", i)].copy()
            if nodo in self.coincidence.keys():
                for nodo2 in self.coincidence[nodo]: self.nodos_cambiados(nodo2, color, s)
        return s
                
    # Grafo no dirigido simple
    def add_arista(self, nodo1, nodo2):
        if not nodo1.id in self.nodos.keys():
            self.add_nodo(nodo1)
        if not nodo2.id in self.nodos.keys():
            self.add_nodo(nodo2)
        
        # Comprobamos que no se pierda factibilidad
        if (nodo1.color is not None) and (nodo1.color == nodo2.color):
            raise SolucionNoFactible("La arista añadida une dos elementos con el mismo color")
            
        nodo1.adyacentes.add(nodo2.id)
        nodo2.adyacentes.add(nodo1.id)
    
    def copy(self):
        grafo = Grafo(self.colores, self.before, self.after, self.coincidence)
        for nodo in self.nodos.values():
            grafo.add_nodo(nodo.copy())
        return grafo


# Estructuras de datos para el problema

class Periodo():
    def __init__(self, i, line):
        self.id = i
        datos = line.split(", ")
        self.dia = datos[0]
        self.hora = datos[1]
        self.length = int(datos[2])
        self.frontload = 0
        self.penalizacion = float(datos[3])
        
    def __repr__(self):
        return f"{self.id}. Penalizacion:{self.penalizacion}"
 
    
class Estudiante():
    def __init__(self, i, m):
        self.id = i
        self.examenes = []
        
    def __repr__(self):
        return f"{self.id}. Examenes: {self.examenes}"
    
    
class Examen():
    def __init__(self, i, m, line, estudiantes):
        self.id = i
        datos = line.split(", ")
        self.length = int(datos[0])
        self.size = len(datos)-1
        self.frontload = 0
        self.estudiantes = set()
        for i in range(1,len(datos)):
            id_est = int(datos[i])
            self.estudiantes.add(id_est)
            if not(id_est in estudiantes.keys()):
                estudiantes[id_est] = Estudiante(id_est, m)
            estudiantes[id_est].examenes.append(self.id)
        
        def __repr__(self):
            return f"{self.id}."
            
    
class Sala():
    def __init__(self, i, line):
        self.id = i
        datos = line.split(", ")
        self.size = int(datos[0])
        self.penalizacion = float(datos[1])
        
    def __repr__(self):
        return f"{self.id}. Size:{self.size}"
    

class Problema():
    def __init__(self, file):
        with open(file, "r") as f:
            line = f.readline().strip()
            while line != "":
                if (line[:7] == "[Exams:"):
                    self.examenes = []
                    self.estudiantes = {}
                    m = int(line[7:-1])
                    for i in range(m):
                        line = f.readline().strip()
                        self.examenes.append(Examen(i, m, line, self.estudiantes))
                
                elif (line[:9] == "[Periods:"):
                    self.periodos = []
                    self.dias = {}
                    self.colores = set()
                    m = int(line[9:-1])
                    for i in range(m):
                        line = f.readline().strip()
                        p = Periodo(i, line)
                        self.periodos.append(p)
                        self.colores.add(i)
                        if not(p.dia) in self.dias.keys():
                            self.dias[p.dia] = []
                        self.dias[p.dia].append(i)
                        
                        
                elif (line[:7] == "[Rooms:"):
                    self.salas = []
                    m = int(line[7:-1])
                    for i in range(m):
                        line = f.readline().strip()
                        self.salas.append(Sala(i, line))
                
                if (line == "[PeriodHardConstraints]"):
                    line = f.readline().strip()
                    self.after = {}
                    self.before = {}
                    self.coincidence = {}
                    self.exclusion = []
                    while line != "[RoomHardConstraints]":
                        e1, tipo, e2 = line.split(", ")
                        e1, e2 = int(e1), int(e2)
                        if tipo == "AFTER":
                            if not(e1 in self.after.keys()): self.after[e1] = set()
                            self.after[e1].add(e2)
                            if not(e2 in self.before.keys()): self.before[e2] = set()
                            self.before[e2].add(e1)
                        elif tipo == "EXAM_COINCIDENCE":
                            if not(e1 in self.coincidence.keys()): self.coincidence[e1] = set()
                            self.coincidence[e1].add(e2)
                            if not(e2 in self.coincidence.keys()): self.coincidence[e2] = set()
                            self.coincidence[e2].add(e1)
                        elif tipo == "EXCLUSION":
                            self.exclusion.append( (e1,e2) )
                        line = f.readline().strip()
                
                if (line == "[RoomHardConstraints]"):
                    line = f.readline().strip()
                    self.exclusive = set()
                    while line != "[InstitutionalWeightings]":
                        e1, tipo = line.split(", ")
                        e1 = int(e1)
                        self.exclusive.add(e1)
                        line = f.readline().strip()
                
                if (line == "[InstitutionalWeightings]"):
                    self.TWOINAROW = float(f.readline().strip().split(",")[1])
                    self.TWOINADAY = float(f.readline().strip().split(",")[1])
                    self.gap = int(f.readline().strip().split(",")[1])
                    self.PERIODSPREAD = 1 # Por simplicidad, no lo añaden al conjunto de datos y se queda en 1 por defecto
                    self.NONMIXEDDURATIONS = float(f.readline().strip().split(",")[1])
                    frontload = f.readline().strip().split(",")[1:]
                    self.FRONTLOAD = [int(frontload[0]), int(frontload[1]), float(frontload[2])]
                
                line = f.readline().strip()
                
        examenes_por_tam = sorted(self.examenes, key = lambda e: (e.size,e.id) , reverse = True)[:self.FRONTLOAD[0]]
        self.examenes_grandes = {ex.id for ex in examenes_por_tam}
    
    def generarGrafo(self):
        # Primera Fase: Asignar los horarios a cada examen ignorando las salas
        # Se genera el grafo que modeliza el problema restringido a la asignacion de los periodos
        grafo = Grafo(self.colores, self.before, self.after, self.coincidence)
        
        # Añadimos un nodo por cada examen y cada periodo
        for p in self.periodos:
            grafo.add_nodo( Nodo(("color", p.id), "periodo", p, p.id) )
        
        for e in self.examenes:
            e.nodo = Nodo(e.id, "examen", e)
            grafo.add_nodo(e.nodo)
            # Añadimos las restricciones del limite de tiempo de los horarios
            for p in self.periodos:
                if e.length > p.length:
                    grafo.add_arista(grafo.nodos[e.id], grafo.nodos[("color", p.id)] )
        
        # Añadimos las restricciones para evitar conflictos
        for e in self.estudiantes.values():
            for i in range(len(e.examenes)):
                for j in range(i+1, len(e.examenes)):
                    id_examen1 = e.examenes[i]
                    id_examen2 = e.examenes[j]
                    grafo.add_arista(grafo.nodos[id_examen1], grafo.nodos[id_examen2]) 
        
        # Añadimos las restricciones de exclusion
        for e1, e2 in self.exclusion:
            grafo.add_arista(grafo.nodos[e1], grafo.nodos[e2])
        
        # Añadimos restricciones previas para after, que se completaran dinamicamente
        for e1 in self.after.keys():
            grafo.add_arista(grafo.nodos[e1], grafo.nodos[("color", min(grafo.colores))] )
            for e2 in self.after[e1]:
                grafo.add_arista(grafo.nodos[e1], grafo.nodos[e2])
                grafo.add_arista(grafo.nodos[e2], grafo.nodos[("color", max(grafo.colores))] )
        
        self.grafo = grafo

    # Modifica los datos del problema a través de los datos del grafo
    def asignacionPeriodos(self, grafo):        
        for p in self.periodos:
            aux = set( filter(lambda n: grafo.nodos[n].tipo == "examen", grafo.nodos_por_color[p.id]) )
            p.estudiantes = set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in aux])
            p.examenes = {nodo_id for nodo_id in aux}
    
    # Obtiene los datos asociados al grafo, pero sin modificar el problema
    def obtenerPeriodos(self, grafo, periodos = None):
        if periodos is None: periodos = grafo.colores
        d = {}
        for p in periodos:
            aux = set( filter(lambda n: grafo.nodos[n].tipo == "examen", grafo.nodos_por_color[p]) )
            d[p] = {"dia" : self.periodos[p].dia,
                    "estudiantes" : set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in aux]),
                    "examenes": {id_nodo for id_nodo in aux} }
        return d
    
    
    # Consideramos unicamente las penalizaciones asociadas a los periodos
    def f_objFase1(self, grafo, **kargs):
        d = self.obtenerPeriodos(grafo)
        dia = (None,[])
        spread = []
        front = max(self.colores) - self.FRONTLOAD[1]
        C2R, C2D, CPS, CFL, CP = 0, 0, 0, 0, 0       
        for p in d.keys():
            # PERIODPENALTY
            CP += len(d[p]["examenes"]) * self.periodos[p].penalizacion
            # TWOINADAY y TWOINAROW (son excluyentes, de ahi el []:-1])
            if d[p]["dia"] == dia[0]:
                if dia[1] != []:
                    C2R += len(d[p]["estudiantes"] & d[dia[1][-1]]["estudiantes"])
                for p2 in dia[1][:-1]:
                    C2D += len(d[p]["estudiantes"] & d[p2]["estudiantes"])
                dia[1].append(p)
            else:
                dia = (d[p]["dia"], [p])
            # PERIODSPREAD
            for p2 in spread:
                CPS += len(d[p]["estudiantes"] & d[p2]["estudiantes"])
            if len(spread)>= self.gap:
                spread.pop(0)
            spread.append(p)
            # FRONTLOAD
            if p > front:
                CFL += len(self.examenes_grandes & d[p]["examenes"])
        return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CP
    
    # Calcula el incremento que ha supuesto añadir el color a un nodo (y sus coincidentes) de forma mas eficiente que la funcion objetivo 
    def inc_Fase1(self, grafo, nodo, color, colores_evaluados = None, **kargs):
        if colores_evaluados is None: colores_evaluados = set()
        if color is None or nodo in colores_evaluados: return 0
        colores_evaluados.add(nodo)
        dia = set(self.dias[self.periodos[color].dia]) - {color}
        spread = set(range(color-self.gap, color+self.gap+1)) & self.colores - {color}
        d = self.obtenerPeriodos(grafo, dia | spread)
        C2R, C2D, CPS, CFL = 0, 0, 0, 0
        
        # PERIODPENALTY
        CP = self.periodos[color].penalizacion
        # FRONTLOAD
        if (color > max(self.colores) - self.FRONTLOAD[1]) and (grafo.nodos[nodo].id in self.examenes_grandes): CFL = 1
        for p2 in d.keys():
            # TWOINADAY y TWOINAROW
            if p2 in dia:
                if (p2 == color -1) or (p2 == color +1):  C2R += len(self.examenes[nodo].estudiantes & d[p2]["estudiantes"])
                else: C2D += len(self.examenes[nodo].estudiantes& d[p2]["estudiantes"])
            # PERIODSPREAD
            if p2 in spread and p2 != color: CPS += len(self.examenes[nodo].estudiantes & d[p2]["estudiantes"])
        inc = C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CP
        if nodo in self.coincidence.keys(): 
            for nodo2 in self.coincidence[grafo.nodos[nodo].id]: inc += self.inc_Fase1(grafo, nodo2, color, colores_evaluados)
        return inc
    
        
    
"""    def f_obj(self, grafo = None):
        if grafo is None:
            try:
                grafo = self.grafo
            except:
                self.generarGrafo()
                grafo = self.grafo
                
        asigPeriodo = self.asignacionPeriodos(grafo)
        C2R, C2D, CPS, CMD, CFL, CP, CR = 0, 0, 0, 0, 0, 0, 0
        
        for p in self.periodos:
            if p.id in asigPeriodo.keys(): CP += p.penalizacion * len(asigPeriodo[p.id])
            

        for s in self.estudiantes.values():
            for i,e1_id in enumerate(s.examenes):
                e1 = self.examenes[e1_id]
                if e1.nodo.color is None:
                    continue
                p1 = self.periodos[e1.nodo.color]
                for e2_id in s.examenes[i+1:]:
                    e2 = self.examenes[e2_id]
                    if e2.nodo.color is None:
                        continue
                    p2 = self.periodos[e2.nodo.color]
                    if p1.dia == p2.dia:
                        if abs(p1.id - p2.id) == 1: C2R += 1
                        else: C2D +=1
                    if 0 < abs(p1.id -p2.id) <= self.gap: CPS += 1
        # Falta añadir mixedDurations y sala penalty
        # for sala in sala... sala como un dic de periodos
        for e in self.examenes_grandes:
            if (e.nodo.color is not None) and e.nodo.color > (self.periodos[-1].id-self.FRONTLOAD[1]): CFL +=1
        for p in self.periodos:
            if p.id in asigPeriodo.keys(): CP += p.penalizacion * len(asigPeriodo[p.id])
        
        return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CMD*self.NONMIXEDDURATIONS + CFL*self.FRONTLOAD[2] + CP + CR"""
    
if __name__ == "__main__":
    # Lectura de los datos del problema
    file = "set1.txt"
    P = Problema(file)
    
    # Primera Fase: asignar periodos/horarios ignorando las salas por el momento
    P.generarGrafo()
    grafo = P.grafo.copy()
    f_obj = P.f_objFase1
    f_heur = P.inc_Fase1
    heuristicas = [GHH.LargestDegree, GHH.LargestSaturationDegree, GHH.LargestColorDegree, GHH.LargestWeightedDegree, GHH.LargestEnrollment, GHH.Random]
    
    n = ceil( len(grafo.nodos_por_color[None])/2 )
    porcentaje = 10     # Considerar un movimiento que cambie el porcentaje% de los elementos de la lista
    movimientos = [ lambda x, h: GHH.repetirMov(GHH.cambiarVarios, x, h, m, 1) for m in [2, ceil(n*porcentaje/100)]]
    hl_inicial = [GHH.LargestSaturationDegree] * n

    import time
    a = time.time()    
    HH = GHH.GHH(grafo, heuristicas, movimientos, f_obj, f_heur, 5, 9, hl_inicial)
    print(time.time() - a)
    print(HH.mejor_val) 
    
    a = time.time()    
    HH.iteracion()
    print(time.time() - a)
    print(HH.mejor_val)
    
    # a = time.time()    
    # HH.iterar(len(grafo.nodos_por_color[None]) * 5)
    # print(time.time() - a)
    # print(HH.mejor_val)
    # P.asignacionPeriodos(HH.grafo)
    
    # Segunda Fase: asignar las salas conocidos los periodos asignados
    

















        
