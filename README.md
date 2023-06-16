# Trabajo-Fin-de-Grado

## Archivos de ITC2007
  Estos archivos corresponden con los ofrecidos por la competición ITC2007. Debido a que la página de la competición se encuentra caída en la actualidad, he subido aquí estos archivos para facilitar su acceso.
  La página puede ser visitada haciendo uso de la web WayBack Machine, que recopila el estado de las webs antiguas para garantizar su acceso en el futuro, mediante el siguiente enlace: https://web.archive.org/web/20090706131749/http://www.cs.qub.ac.uk/itc2007/
  - InstanciasITC2007.zip   contiene los el conjunto de datos de la competicion. El formato de los archivos es .exam, pero pueden ser tratados como .txt
  - ModeloITC2007.pdf       es el artículo donde se explica el modelo de problema (i. e. Las restricciones que se deben cumplir y la función objetivo)


## Algoritmo para la resolución de ITC2007
  El algoritmo está dividido en dos archivos, uno que corresponde a la propia Graph-HiperHeuristic (GHH) y otro que corresponde a la modelización de ITC 2007 y la aplicación de GHH sobre estos datos
  - GHH.py                  contiene la hiperheurística mencionada, es aplicable a problemas distintos de los de ITC2007
  - ITC2007.py              contiene la modelización y aplicación de GHH. La misma modelización no será, en general, aplicable a otros problemas


## Metaheurísticas
  Se añade la implementación de las metaheuristicas desarrolladas en el trabajo a modo de ejemplo
  - TabuSearch.py           corresponde con la implementación de una búsqueda tabú. A modo de ejemplo, esta comentado como se aplicaría esta a la resolución del problema de la mochila 0-1
