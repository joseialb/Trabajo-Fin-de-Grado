import numpy as np
import random
from GHH import SolucionNoFactible
import GHH
from math import ceil
import copy
import time

"""
Formato de datos de ITC 2007
"""

 
# Estructuras de datos para grafos

class Nodo():
    def __init__(self, n_id, tipo, objeto, color = None, adyacentes = None, colores_vecinos = None):
        self.id = n_id
        self.tipo = tipo
        self.objeto = objeto
        self.color = color
        self.adyacentes = set() if adyacentes is None else adyacentes
        self.colores_vecinos = set() if colores_vecinos is None else colores_vecinos
    
    def __repr__(self):
        return f"{self.id}: {self.color}"
    
    def copy(self):
        return Nodo(self.id, self.tipo, self.objeto, self.color, self.adyacentes.copy(), self.colores_vecinos.copy())
    
    def peso(self):
        if self.tipo == "examen":
            s = self.objeto.size
        else: raise Exception("Se ha pedido el peso de un nodo que no es un examen")
        return s
    
            
class Grafo():
    def __init__(self, periodos, salas, **kargs):
        self.nodos = {}        
        self.salas = salas
        self.periodos = periodos
        self.colores = { (p,r) for p in periodos for r in salas}
        
        self.nodos_por_sala = { r: set() for r in salas | {None}}
        self.nodos_por_periodo = { p: set() for p in periodos | {None}}
        self.nodos_por_color = {(p, r): set() for p in periodos for r in salas}
        self.nodos_por_color[None] = set()
        self.nodos_por_tipo = {"examen" : set(), "exclusivo" : set(), "color" : set(), "periodo" : set()}
        
        self.before = kargs.get("before", {})
        self.after =  kargs.get("after", {})
        self.coincidence = kargs.get("coincidence", {})
        
        self.cap_libre  = kargs.get("cap_libre", {})
        self.duraciones = kargs.get("duraciones", {})
        self.exclusivos = kargs.get("exclusivos", {})
        
        self.nodos_por_tam = []
        self.estudiantes_por_periodo = {i:set() for i in self.periodos}
                      
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
        for nodo in self.nodos_por_tipo["examen"]:
            for nodo2 in self.nodos[nodo].adyacentes:
                if not (nodo2, nodo) in a: a.add( (nodo, nodo2) )
        for nodo in self.nodos_por_tipo["exclusivo"]:
            for nodo2 in self.nodos[nodo].adyacentes:
                if not (nodo2, nodo) in a: a.add( (nodo, nodo2) )
        return a
    
    # Para representar mejor el grado debido a las diferentes aristas posibles
    def grado(self, id1):
        g = 0
        for id2 in self.nodos[id1].adyacentes:
            nodo2 = self.nodos[id2]
            if nodo2.tipo == "examen" or nodo2.tipo == "periodo": g+= len(self.salas)
            else: g += 1 
        return g
    
    def gradoColor(self, id1):
        g = 0
        for id2 in self.nodos[id1].adyacentes - self.nodos_por_color[None]:
            nodo2 = self.nodos[id2]
            if nodo2.tipo == "examen": g+= len(self.salas)
            elif nodo2.tipo == "periodo": g+= len(self.salas)
            elif nodo2.tipo == "exclusivo":
                if nodo2.color is not None: g += 1
            else: g += 1 
        return g
    
    def gradoRestricciones(self, id1, coincidence_visitados = None):
        extra = 0
        if id1 in self.exclusivos: extra = len(self.nodos_por_tipo["examen"])
        if id1 in self.before: extra = len(self.before[id1]) * len(self.colores)//2
        if id1 in self.after: extra = len(self.after[id1]) * len(self.colores)//2
        if id1 in self.coincidence:
            if coincidence_visitados is None: coincidence_visitados = {id1}
            else: coincidence_visitados.add(id1)
            for id2 in self.coincidence[id1]: 
                if not id2 in coincidence_visitados: extra += self.gradoRestricciones(id2, coincidence_visitados)
        return self.grado(id1) + extra
    
    def add_nodo(self, nodo):
        self.nodos[nodo.id] = nodo
        self.nodos_por_tipo[nodo.tipo].add(nodo.id)
        if nodo.tipo == "examen":
            if nodo.color is None:
                self.nodos_por_sala[None].add(nodo.id) 
                self.nodos_por_periodo[None].add(nodo.id)
                self.nodos_por_color[None].add(nodo.id)
            else:
                p, r = nodo.color
                self.nodos_por_sala[r].add(nodo.id)
                self.nodos_por_periodo[p].add(nodo.id)  
                self.nodos_por_color[nodo.color].add(nodo.id)

    # Grafo no dirigido simple
    def add_arista(self, id1, id2):
        nodo1 = self.nodos[id1]
        nodo2 = self.nodos[id2]
        # Solo se comprueba la factibilidad cuando al menos uno de ellos es de tipo examen, ya que en otro caso ya tendran color asignado o son exclusivos, en cuyo caso los exclusivos solo se unen a examenes
        if nodo1.tipo == "examen" or nodo2.tipo == "examen": 
            if nodo1.tipo == "examen" and nodo2.tipo == "examen":
                # Si ambos estan coloreados, comprobamos que no se pierda factibilidad al introducir la arista
                if (nodo1.color is not None) and (nodo2.color is not None):
                    if (nodo1.color[0] == nodo2.color[0]): raise SolucionNoFactible("La arista añadida une dos examenes en el mismo periodo")
                # En otro caso, añadimos los colores a colores_vecinos y comprobamos que siga teniendo posibilidad de ser asignado
                elif nodo1.color is not None:
                    for r in self.salas: nodo2.colores_vecinos.add( (nodo1.color[0], r) )
                    if len(nodo2.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al segundo nodo")
                elif nodo2.color is not None:
                    for r in self.salas: nodo1.colores_vecinos.add( (nodo2.color[0], r) )
                    if len(nodo1.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al primer nodo")
                
            else:
                if nodo1.tipo != "examen": nodo1, nodo2 = nodo2, nodo1  # Aseguramos que el del examen este en primera posicion por simplicidad
                # Si el segundo tipo es un periodo, se añade una arista por cada sala
                if nodo2.tipo == "periodo":          
                    if nodo1.color is not None:
                        if (nodo1.color[0] == nodo2.color): raise SolucionNoFactible("La arista añadida representa la prohibicion de asignar al examen el periodo al que ya esta asignado")
                    else:
                        for r in self.salas: nodo1.colores_vecinos.add( (nodo2.color, r) )
                        if len(nodo1.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al examen")
                
                elif nodo2.tipo == "color":
                    if nodo1.color is not None:
                        if (nodo1.color == nodo2.color): raise SolucionNoFactible("La arista añadida representa la prohibicion de asignar al examen el color al que ya esta asignado")
                    else:
                        nodo1.colores_vecinos.add( nodo2.color )
                        if len(nodo1.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al examen")
                
                elif nodo2.tipo == "exclusivo":
                    # Si ambos estan coloreados, comprobamos que no se pierda factibilidad al introducir la arista
                    if (nodo1.color is not None) and (nodo2.color is not None):
                        if (nodo1.color == nodo2.color): raise SolucionNoFactible("La arista añadida une un examenes asignado al mismo color que un examen exclusivo")
                    # En otro caso, añadimos los colores a colores_vecinos del nodo asociado al examen y comprobamos que siga teniendo posibilidad de ser asignado
                    elif nodo1.color is not None:
                        nodoExamen2 = self.nodos[nodo2.id[0]]
                        nodoExamen2.colores_vecinos.add( nodo1.color )
                        if len(nodoExamen2.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al nodo exclusivo")
                    elif nodo2.color is not None:
                        nodo1.colores_vecinos.add( nodo2.color )
                        if len(nodo1.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("La arista añadida deja sin posibles colores al nodo no exclusivo")
        
        # Finalmente, cada nodo se añade a los adyacentes del otro
        nodo1.adyacentes.add(nodo2.id)
        nodo2.adyacentes.add(nodo1.id)
    
    # Solo se va a colorear nodos de tipo examen
    def colorear(self, nodo, color):
        assert nodo.tipo == "examen", "Se ha intentado colorear un nodo que no es de tipo examen"
        assert color is not None, "No se puede colorear de None pues afecta a las aristas que hay que quitar de forma poco eficiente"            
        if nodo.color == color: return
        cambios = {}
        bool_color, bool_duraciones, bool_capacidad = False, False, False
        
        p, r = color 
        color_anterior = nodo.color
        if color_anterior is None: p_anterior, r_anterior = [None, None]
        else: p_anterior, r_anterior = color_anterior 
        
        try:    
            if color in nodo.colores_vecinos:
                raise SolucionNoFactible("El color indicado coincide con un color prohibido")
            else:
                # Cambiamos el color del nodo guardando una copia para poder revertir
                cambios[nodo.id] = nodo.copy()
                nodo.color = color
                
                # Se cambian los datos de los nodos por color                
                bool_color = True
                self.nodos_por_color[color_anterior].remove(nodo.id)
                self.nodos_por_color[color].add(nodo.id)
                self.nodos_por_periodo[p_anterior].remove(nodo.id)
                self.nodos_por_periodo[p].add(nodo.id)
                self.nodos_por_sala[r_anterior].remove(nodo.id)
                self.nodos_por_sala[r].add(nodo.id)
                self.estudiantes_por_periodo[p].update(nodo.objeto.estudiantes)  # Esto se puede revertir ya que cada estudiante solo puede estar una vez en cada periodo
                if p_anterior is not None: self.estudiantes_por_periodo[p_anterior].difference_update(nodo.objeto.estudiantes)
                # Se añade el color a los colores de los adyacentes
                for id2 in nodo.adyacentes:
                    nodo2 = self.nodos[id2]
                    if (nodo2.color is None):
                        if nodo2.tipo == "examen":
                            if not id2 in cambios.keys(): cambios[nodo2.id] = nodo2.copy()
                            for r in self.salas: nodo2.colores_vecinos.add( (color[0], r) )
                            if len(nodo2.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("El color añadido deja sin posibles periodos a un examen adyacente")
                        elif nodo2.tipo == "exclusivo":
                            nodo2Examen = self.nodos[nodo2.id[0]]
                            if not id2 in cambios.keys(): cambios[nodo2Examen.id] = nodo2Examen.copy()
                            nodo2Examen.colores_vecinos.add(color)
                            if len(nodo2Examen.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("El color añadido deja sin posibles colores a un examen exclusivo")
                        # Si es de tipo de nodo2 es periodo o color no se hace nada pues no van a coincidir al estar en colores_vecinos y tienen color distinto de None
                    
                # Se colorea el exclusivo asociado
                if nodo.id in self.exclusivos.keys():
                    nodo_ex = self.exclusivos[nodo.id]
                    if not id2 in cambios.keys(): cambios[nodo_ex.id] = nodo_ex.copy()
                    nodo_ex.color = color
                    for id2 in self.nodos_por_tipo["examen"] - {nodo.id}:
                        nodo2 = self.nodos[id2]
                        if (nodo2.color is None):
                            if not id2 in cambios.keys(): cambios[nodo2.id] = nodo2.copy()
                            nodo2.colores_vecinos.add( color )
                            if len(nodo2.colores_vecinos) >= len(self.colores): raise SolucionNoFactible("El color añadido al nodo exclusivo deja sin posibles colores a un examen")    
                
                # Restricciones COINCIDENCE
                if nodo.id in self.coincidence.keys():
                    for id2 in self.coincidence[nodo.id]:
                        nodo2 = self.nodos[id2]
                        if nodo2.color is not None: continue
                        if not id2 in cambios.keys(): cambios[id2] = nodo2.copy()    
                        for p in self.periodos - {color[0]}:
                            # cambios[(p,)] = self.nodos[(p,)].copy() # En principio no hace falta
                            self.add_arista(id2, (p,))
                            # add_arista se encarga de añadir los colores y revisar la factibilidad

                # Restricciones AFTER (before y after)
                if nodo.id in self.before.keys():
                    for id2 in self.before[nodo.id]:
                        nodo2 = self.nodos[id2]
                        if nodo2.color is not None: continue
                        if not id2 in cambios.keys(): cambios[id2] = nodo2.copy()    
                        for p in filter(lambda x : x < color[0], self.periodos):
                            # cambios[(p,)] = self.nodos[(p,)].copy() # En principio no hace falta
                            self.add_arista(id2, (p,))
                            # add_arista se encarga de añadir los colores y revisar la factibilidad

                if nodo.id in self.after.keys():
                    for id2 in self.after[nodo.id]:
                        nodo2 = self.nodos[id2]
                        if nodo2.color is not None: continue
                        if not id2 in cambios.keys(): cambios[id2] = nodo2.copy()    
                        for p in filter(lambda x : x > color[0], self.periodos):
                            # cambios[(p,)] = self.nodos[(p,)].copy() # En principio no hace falta
                            self.add_arista(id2, (p,))
                            # add_arista se encarga de añadir los colores y revisar la factibilidad
        
                # Restricciones de capacidad
                if self.cap_libre[color] < nodo.peso():
                    print("Esto no deberia ocurrir NUNCA", nodo, nodo.peso(), self.cap_libre[color])
                    raise SolucionNoFactible("El color indicado supera la capacidad de la sala")    
                self.cap_libre[color] -= nodo.peso()
                bool_capacidad = True
                for id2 in self.nodos_por_tam:                                                           # Mejora de eficiencia si guardamos examenes ordenados por capacidad
                    nodo2 = self.nodos[id2]
                    if nodo2.peso() > self.cap_libre[color]:
                        if nodo2.color is None:
                            if not id2 in cambios.keys(): cambios[id2] = self.nodos[id2].copy()
                            self.add_arista(id2, color)
                            # add_arista se encarga de añadir los colores y revisar la factibilidad
                    else:
                        break                
                
                # Actualizacion de las duraciones
                if not color in self.duraciones.keys(): self.duraciones[color] = {}
                if not nodo.objeto.length in self.duraciones[color].keys(): self.duraciones[color][nodo.objeto.length] = 0
                self.duraciones[color][nodo.objeto.length] += 1
                bool_duraciones = True
            return (nodo, color, color_anterior, cambios, bool_color, bool_capacidad, bool_duraciones)
        
        except SolucionNoFactible as e:
            # Si se lanza una excepcion, se le añaden los datos cambiados para permitir revertir y no alterar el grafo
            raise SolucionNoFactible(e.message,  (nodo, color, color_anterior, cambios, bool_color, bool_capacidad, bool_duraciones))

    
    # Se revierten los cambios realizados (permite ahorrar copias y por tanto ganar eficiencia)
    def revertirCambios(self, datos):
        nodo, color, color_anterior, cambios, bool_color, bool_capacidad, bool_duraciones = datos
        p, r = color 
        if color_anterior is None: p_anterior, r_anterior = [None, None]
        else: p_anterior, r_anterior = color_anterior 
        if bool_duraciones: self.duraciones[color][nodo.objeto.length] -= 1                
        if bool_capacidad: self.cap_libre[color] += nodo.peso()
        if bool_color:
            nodo.color = color_anterior
            self.nodos_por_color[color].remove(nodo.id)
            self.nodos_por_color[color_anterior].add(nodo.id)
            self.nodos_por_periodo[p].remove(nodo.id)
            self.nodos_por_periodo[p_anterior].add(nodo.id)
            self.nodos_por_sala[r].remove(nodo.id)
            self.nodos_por_sala[r_anterior].add(nodo.id)
            self.estudiantes_por_periodo[p].difference_update(nodo.objeto.estudiantes)
            if p_anterior is not None: self.estudiantes_por_periodo[p_anterior].update(nodo.objeto.estudiantes)
        for id2, nodoCopia in cambios.items():
            self.nodos[id2] = nodoCopia


    def copy(self):
        grafoCopia = Grafo(self.periodos, self.salas, before = self.before, after = self.after, coincidence = self.coincidence,
                           cap_libre = self.cap_libre.copy(), duraciones = copy.deepcopy(self.duraciones), exclusivos = self.exclusivos)
        grafoCopia.nodos_por_tam = self.nodos_por_tam
        for nodo in self.nodos.values():
            grafoCopia.add_nodo(nodo.copy())
        return grafoCopia


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
                    self.idsPeriodos = set()
                    self.dias = {}
                    m = int(line[9:-1])
                    for i in range(m):
                        line = f.readline().strip()
                        p = Periodo(i, line)
                        self.periodos.append(p)
                        self.idsPeriodos.add(i)
                        if not(p.dia) in self.dias.keys():
                            self.dias[p.dia] = []
                        self.dias[p.dia].append(i)                                             
                        
                elif (line[:7] == "[Rooms:"):
                    self.salas = []
                    self.idsSalas = set()
                    self.capacidades = {}
                    m = int(line[7:-1])
                    for i in range(m):
                        line = f.readline().strip()
                        r = Sala(i, line)
                        self.salas.append(r)
                        self.idsSalas.add(i)
                        self.capacidades[i] = r.size
                
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
                    self.exclusivos = set()
                    while line != "[InstitutionalWeightings]":
                        e1, tipo = line.split(", ")
                        e1 = int(e1)
                        self.exclusivos.add(e1)
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
        self.grafo = Grafo(self.idsPeriodos, self.idsSalas, before = self.before, after = self.after, coincidence = self.coincidence,
                           cap_libre = {(p,r) : self.capacidades[r] for p in self.idsPeriodos for r in self.idsSalas})
        
        # Añadimos un nodo por cada examen, por cada exclusivo, por cada periodo y cada par (periodo, sala)
        for p in self.periodos:
            self.grafo.add_nodo( Nodo((p.id,), "periodo", p, p.id) )
            for r in self.salas:
                self.grafo.add_nodo( Nodo((p.id,r.id), "color", (p,r), (p.id,r.id)) )
        
        for e in self.examenes:
            e.nodo = Nodo(e.id, "examen", e)
            self.grafo.add_nodo(e.nodo)
            if e.id in self.exclusivos:
                nodo_ex = Nodo( (e.id,"exclusivo"), "exclusivo", None)
                self.grafo.exclusivos[e.id] = nodo_ex
                self.grafo.add_nodo(nodo_ex)
                            
            # Añadimos las restricciones del limite de tiempo de los horarios
            for p in self.periodos:
                if e.length > p.length:
                    self.grafo.add_arista(e.id, (p.id,))
        
        # Cada nodo exclusivo se une a todos los demás nodos de examen para establecer la obligación de estar en salas distintas
        for nodo_ex in self.grafo.nodos_por_tipo["exclusivo"]:
            for nodo in self.grafo.nodos_por_tipo["examen"]:
                if nodo != nodo_ex[0]: self.grafo.add_arista(nodo, nodo_ex)
                
        # Añadimos las restricciones para evitar conflictos
        for e in self.estudiantes.values():
            for i in range(len(e.examenes)):
                for j in range(i+1, len(e.examenes)):
                    id_examen1 = e.examenes[i]
                    id_examen2 = e.examenes[j]
                    self.grafo.add_arista(id_examen1, id_examen2) 
        
        # Añadimos las restricciones de exclusion
        for e1, e2 in self.exclusion:
            self.grafo.add_arista(e1,e2)
        
        # Añadimos restricciones previas para las restricciones AFTER. No son estrictamente necesarias (si ponemos el <= en la funcion de colorear) pero añadirlas completa la nocion de dificultad a la hora de elegir el nodo mediante LargestDegree y demás
        for e1 in self.after.keys():
            self.grafo.add_arista(e1, (min(self.idsPeriodos),))
            for e2 in self.after[e1]:
                self.grafo.add_arista(e1, e2)
                self.grafo.add_arista(e2, (max(self.idsPeriodos),))
        
        # Se añaden las restricciones de capacidad de las salas
        for e in self.examenes:
            for r in self.salas:
                if e.size > r.size:
                    for p in self.periodos: self.grafo.add_arista( e.id, (p.id, r.id) )
        
        self.grafo.nodos_por_tam = sorted([ eid  for eid in self.grafo.nodos_por_tipo["examen"]] , key = lambda i: self.grafo.nodos[i].peso(), reverse = True)


    # La función que determina el valor completo de la solución aportada por un grafo
    def f_objGrafo(self, grafo, **kargs):
        dia = (None,[])
        spread = []
        front = max(self.idsPeriodos) - self.FRONTLOAD[1]
        # estudiantes_por_periodo = {}                            # Para mas eficiencia, esto podria guardarse en los datos del grafo actualizandolo cada vez que se actualiza nodo por periodo
        C2R, C2D, CPS, CFL, CP, CR, CNM = 0, 0, 0, 0, 0, 0, 0
        
        for p in self.periodos:
            # estudiantes_por_periodo[p.id] = set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in grafo.nodos_por_periodo[p.id]])
            # PERIODPENALTY
            CP += len(grafo.nodos_por_periodo[p.id]) * self.periodos[p.id].penalizacion
            # TWOINADAY y TWOINAROW (son excluyentes, de ahi el [:-1])
            if p.dia == dia[0]:
                if dia[1] != []:
                    C2R += len(grafo.estudiantes_por_periodo[p.id] & grafo.estudiantes_por_periodo[dia[1][-1].id])
                for p2 in dia[1][:-1]:
                    C2D += len(grafo.estudiantes_por_periodo[p.id] & grafo.estudiantes_por_periodo[p2.id])
                dia[1].append(p)
            else:
                dia = (p.dia, [p])
            # PERIODSPREAD
            for p2 in spread:
                CPS += len(grafo.estudiantes_por_periodo[p.id] & grafo.estudiantes_por_periodo[p2.id])
            if len(spread)>= self.gap:
                spread.pop(0)
            spread.append(p)
            # FRONTLOAD
            if p.id > front:
                CFL += len(self.examenes_grandes & grafo.nodos_por_periodo[p.id])
        
        # ROOMPENALTY
        for r in self.salas:
            CR += len(grafo.nodos_por_sala[r.id]) * self.salas[r.id].penalizacion
        
        # NONMIXEDPENALTY
        for d in grafo.duraciones.values():
            CNM += max(0, len([x for x in d.values() if x > 0])-1 )
            
        return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CNM*self.NONMIXEDDURATIONS + CP + CR
    
    
    # # Calcula el incremento de la funcion objetivo que ha supuesto colorear un único nodo de forma mas eficiente que la función objetivo (la cual debe tener en cuenta todos los nodos)
    # def inc_obj(self, grafo, nodo, color):
        
    #     global t2
    #     a = time.time()
        
    #     if color is None: return 0
    #     pid = color[0]
    #     rid = color[1]
    #     dia = set(self.dias[self.periodos[pid].dia]) - {pid}
    #     spread = set(range(pid-self.gap, pid+self.gap+1)) & self.idsPeriodos - {pid}
    #     # estudiantes_por_periodo = {}                            # Para mas eficiencia, esto podria guardarse en los datos del grafo actualizandolo cada vez que se actualiza nodo por periodo
    #     C2R, C2D, CPS, CFL = 0, 0, 0, 0
        
    #     # PERIODPENALTY
    #     CP = self.periodos[pid].penalizacion
        
    #     # FRONTLOAD
    #     if (color[0] > max(self.idsPeriodos) - self.FRONTLOAD[1]) and (grafo.nodos[nodo].id in self.examenes_grandes): CFL = 1
        
    #     for p2 in dia | spread:
    #         # estudiantes_por_periodo[p2] = set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in grafo.nodos_por_periodo[p2]])
    #         # TWOINADAY y TWOINAROW
    #         if p2 in dia:
    #             if (p2 == pid -1) or (p2 == pid +1):  C2R += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])
    #             else: C2D += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])
    #         # PERIODSPREAD
    #         if p2 in spread: CPS += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])

    #     # ROOMPENALTY
    #     CR = self.salas[rid].penalizacion
        
    #     # NONMIXEDPENALTY    
    #     if len([x for x in grafo.duraciones[color].values() if x > 0]) > 1 and grafo.duraciones[color][grafo.nodos[nodo].objeto.length] == 1: CNM = 1
    #     else: CNM = 0
        
        
    #     t2 += time.time()-a
        
    #     return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CNM*self.NONMIXEDDURATIONS + CP + CR 
    
    
    # Calcula el incremento de la funcion objetivo que supondrá colorear un único nodo sin necesidad de colorearlo
    def prediccion_inc_obj(self, grafo, nodo, color):
        if color is None: return 0
        pid = color[0]
        rid = color[1]
        dia = set(self.dias[self.periodos[pid].dia]) - {pid}
        spread = set(range(pid-self.gap, pid+self.gap+1)) & self.idsPeriodos - {pid}
        # estudiantes_por_periodo = {}                            # Para mas eficiencia, esto podria guardarse en los datos del grafo actualizandolo cada vez que se actualiza nodo por periodo
        C2R, C2D, CPS, CFL = 0, 0, 0, 0
        
        # PERIODPENALTY
        CP = self.periodos[pid].penalizacion
        
        # FRONTLOAD
        if (color[0] > max(self.idsPeriodos) - self.FRONTLOAD[1]) and (grafo.nodos[nodo].id in self.examenes_grandes): CFL = 1
        
        for p2 in dia | spread:
            # estudiantes_por_periodo[p2] = set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in grafo.nodos_por_periodo[p2]])
            # TWOINADAY y TWOINAROW
            if p2 in dia:
                if (p2 == pid -1) or (p2 == pid +1):  C2R += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])
                else: C2D += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])
            # PERIODSPREAD
            if p2 in spread: CPS += len(self.examenes[nodo].estudiantes & grafo.estudiantes_por_periodo[p2])

        # ROOMPENALTY
        CR = self.salas[rid].penalizacion
        
        # NONMIXEDPENALTY    
        duracion_nodo = self.examenes[nodo].length
        CNM = 0
        if (color in grafo.duraciones.keys()):
            if not(duracion_nodo in grafo.duraciones[color].keys()) or (grafo.duraciones[color][duracion_nodo] == 0):
                # Si el nodo del examen es el primero de esa duracion y hay al menos otro examen en el periodo y sala con otra duracion distinta
                for duracion, repeticiones in grafo.duraciones[color].items():
                    if repeticiones > 0 and duracion != duracion_nodo:  # Realmente siempre se va a cumplir que duracion != duracion_ex por el if anterior
                        CNM = 1
                        break
        return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CNM*self.NONMIXEDDURATIONS + CP + CR 
    

    # Modifica los datos del problema a través de los datos del grafo
    def asignaciones(self, grafo):        
        for p in self.periodos:
            p.estudiantes = set().union(*[self.examenes[id_nodo].estudiantes for id_nodo in grafo.nodos_por_periodo[p.id]])
            p.examenes = {nodo_id for nodo_id in grafo.nodos_por_periodo[p.id]}
        for r in self.salas:
            r.examenes = {nodo_id for nodo_id in grafo.nodos_por_sala[r.id]}
        for e in self.examenes:
            e.horario = grafo.nodos[e.id].color[0]
            e.sala = grafo.nodos[e.id].color[1]
    
    
    # Calcula el valor de la funcion objetivo solo con los datos del problema, sin depender del grafo
    def f_obj(self):
        dia = (None,[])
        spread = []
        front = max(self.idsPeriodos) - self.FRONTLOAD[1]
        C2R, C2D, CPS, CFL, CNM, CP, CR = 0, 0, 0, 0, 0, 0, 0       
        for p in self.periodos:
            # PERIODPENALTY
            CP += len(p.examenes) * p.penalizacion
            # TWOINADAY y TWOINAROW (son excluyentes, de ahi el []:-1])
            if p.dia == dia[0]:
                if dia[1] != []:
                    C2R += len(p.estudiantes & dia[1][-1].estudiantes)
                for p2 in dia[1][:-1]:
                    C2D += len(p.estudiantes & p2.estudiantes)
                dia[1].append(p)
            else:
                dia = (p.dia, [p])
            # PERIODSPREAD
            for p2 in spread:
                CPS += len(p.estudiantes & p2.estudiantes)
            if len(spread)>= self.gap:
                spread.pop(0)
            spread.append(p)
            # FRONTLOAD
            if p.id > front:
                CFL += len(self.examenes_grandes & p.examenes)
                CR = 0      
            
            for r in self.salas:
                # NONMIXEDPENALTY
                CNM += max(0, len({self.examenes[e].length for e in (r.examenes & p.examenes)})-1 )
                
        for r in self.salas:
            # ROOMPENALTY 
            CR += len(r.examenes) * r.penalizacion
            
        return C2R*self.TWOINAROW + C2D*self.TWOINADAY + CPS*self.PERIODSPREAD + CFL*self.FRONTLOAD[2] + CNM*self.NONMIXEDDURATIONS + CP + CR
    


def generarSolucion(entrada, salida, max_it = 100):
    try:
        P = Problema(entrada)
        
        # Parámetros de la hiperheurística
        e = 2
        tenencia = 9
        n = ceil( len(P.examenes)/e )
        movimientos = [ lambda x, h: GHH.repetirMov(GHH.cambiarVarios, x, h, 2, 3) ]
        heuristicas = [GHH.LargestDegree, GHH.LeastSaturationDegree, GHH.LargestColorDegree, GHH.GradoRestricciones, GHH.LargestWeightedDegree, GHH.LargestEnrollment, GHH.Random]
        hl_inicial = [GHH.LeastSaturationDegree] * n
        # hl_inicial = [GHH.LargestColorDegree] * n
        # hl_inicial = None
        
        # Inicialización
        P.generarGrafo()
        HH = GHH.GHH(P.grafo, heuristicas, movimientos, P.f_objGrafo, P.prediccion_inc_obj, e, tenencia, hl_inicial)
        
        # Iteraciones
        a = time.time()
        HH.iterar(max_it)
        print("Tiempo Total", time.time()-a)
        
        # Calculo de la funcion objetivo y asignaciones del grafo al problema
        P.asignaciones(HH.mejor_sol)    
        valorFinal = P.f_obj()
        # print(f"Valor obtenido: {valorFinal}")
        
        # Guardar resultados
        with open(salida, "w") as file:
            for examen in P.examenes:
                file.write(f"{examen.horario}, {examen.sala}\n")
            file.write(f"\nValor Total: {valorFinal}")
            file.write(f"\Heuristica inicial: LargestDegree")
            file.write(f"\nIteraciones: {HH.i}")
            file.write(f"\nSeleccion de color: Ruleta")
            
                       
            file.write("\n\nNumero de apariciones de cada heuristica:\n")
            nombre_heuristicas =["LargestDegree:         ",
                                 "LeastSaturationDegree: ",
                                 "LargestColorDegree:    ",
                                 "GradoRestricciones:    ",
                                 "LargestWeightedDegree: ",
                                 "LargestEnrollment:     ",
                                 "Random:                "]
            
            for i, h in enumerate(heuristicas):
                apariciones = HH.mejor_h.count(h)
                file.write(f"{nombre_heuristicas[i]}    {apariciones:}  ({100*apariciones/len(HH.mejor_h):.2f}%)\n")
        
    except Exception as e:
        print(e)
        raise HiperHeuristicaFallida("Error raro", HH) from e



class HiperHeuristicaFallida(Exception):
    def __init__(self, msg, HH):
        self.message = msg
        self.HH = HH
        super().__init__(self.message)
    def __repr__(self):
        return self.message


if __name__ == "__main__":
    # Lectura de los datos del problema
    datasets = [f"InstanciasITC2007/set{i}.exam" for i in range(1,13)]
    salidas  = [f"set{i}SaturationBest.sol" for i in range(1,13)] 
    HHs = []
    # Parámetros de la hiperheurística
    
    for i in range(0,12):
        try:
            generarSolucion(datasets[i], salidas[i], 500)
            print("Finalizado datos de ", i+1)
        except HiperHeuristicaFallida as e:
            HHs.append(e.HH)
            print(e)
            print("Algo ha pasao en el dataset ", i+1)
            continue
        
            
        
    
    
    
    
    
    
    
    
    
    























































        
