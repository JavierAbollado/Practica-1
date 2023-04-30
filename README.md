
# Práctica 1

## Índice
 - [Variables globales](#id1)
 - [Main](#id2)
 - [Productor](#id3)
    - [produce](#id3.1)
    - [add_data](#id3.2)
 - [Consumidor](#id4)
    - [consume](#id4.1)
    - [get_min_values](#id4.2)
    - [get_data](#id4.3)
    

## Variables globales <a name=id1></a>

Primero definimos las variables globales del ejercicio. La idea es que vamos a tener ```NPROD``` productores y cada uno de ellos va a generar ```K``` elementos. Además el storage de cada productor tiene un límite ```MAX_STORAGE```.  Finalmente produciremos ```N``` elementos en total.

```python
K = 10              # nº de elemtos a producir (por productor)
MAX_STORAGE = 5     # capacidad máxima del storage
NPROD = 3           # nº de productores
N = K * NPROD       # nº total de elemntos (a introducir en la lista final)
```



## Main <a name=id2></a>

Proceso principal del programa, en él creamos ```NPROD```productores, donde cada uno produce ```K```valores y al final retornaremos la lista con todos los valores ordenados. Todos los productores tienen su propio storage de capacidad máxima ```MAX_STORAGE```. Por lo que si nos quedamos sin espacio en el storage esperaremos a que el consumidor nos quite algún elemento y podamos seguir produciendo.


```python
def main():

    # storage individual para cada productor (valor nulo : -2)
    storages = [Array('i', MAX_STORAGE) for _ in range(NPROD)]
    for s in storages:
        for i in range(MAX_STORAGE):
            s[i] = -2

    # Semaforos : 
    sems_capacity = [BoundedSemaphore(MAX_STORAGE) for _ in range(NPROD)]  # bloquea (el productor) cuando el storage esta lleno
    sems_empty    = [Semaphore(0) for _ in range(NPROD)]                   # bloquea (el consumidor) cuando el storage esta vacío


    # NPROD productores -> cada uno creará K valores (en orden)
    producers = [ Process(target=produce,
                        name='Prod' + (' '*3 + str(index))[-4:],
                        args=(storages[index], sems_capacity[index], sems_empty[index]))
                for index in range(NPROD) ]

    # 1 consumidor : coge en orden todos los valores producidos por los productores 
    consumer = Process(target=consume,
                       name=f"Consumer",
                       args=(storages, sems_capacity, sems_empty))

    # inicializar todos los procesos
    for p in producers + [consumer]:
        p.start()
    for p in producers + [consumer]:
        p.join()
```





## Productor <a name=id3></a>

El productor se encarga de generar elementos siempre y cuando tenga espacio para almacenar el proximo elemento. Para ello definiremos dos funciones principales:


### produce <a name=id3.1></a>

Proceso de producción de todos los ```K```elementos a producir por el productor. Hacemos un bucle en el que en cada iteración crearemos un dato nuevo ```data = last_data + random.randint(1,10)``` y al final de la secuencia generaremos un -1 para indicar al consumidor que hemos finalizado, de ahí la excepción ```if n < K else -1```. Luego lo añadimos al storage (la propia función *add_data* se encarga de tener en cuenta los espacios que tenemos y los avisos respectivos) ```add_data(storage, data, position, sem_capacity, sem_empty)```. 
 
Argumentos:
   - *storage* : array circular donde iremos guardando los elementos generados.
   - *sem_capacity* : semáforo para controlar si el almacén está lleno.
   - *sem_empty* : semáforo para controlar si el almacén está vacío (servira para cuando el consumidor quiera acceder a nuestros datos).
  
Variables:
   - *last_data* : para ir guardando el último dato generado, ya que queremos generar una sucesión creciente de datos.
   - *position* : índice donde toca insertar el siguiente valor (en nuestro array circular).

```python
def produce(storage, sem_capacity, sem_empty): 
    last_data = 0
    position = 0   # índice donde insertar el siguiente valor
    for n in range(K+1):
        # crear nuevos datos
        print (f"\n[{current_process().name}] produciendo")
        data = last_data + random.randint(1,10) if n < K else -1 # end of secuence 
        # añadir datos
        add_data(storage, data, position, sem_capacity, sem_empty)
        print (f"\n[{current_process().name}]\t==>\t| dato : {data}\t| posicion : {position}")
        position = (position + 1) % MAX_STORAGE
        last_data = data
```


### add_data  <a name=id3.2></a>

Se encarga de introducir el dato generado al storage. Primero comprueba que tengamos espacio en nuestro storage ```sem_capacity.acquire()``` y luego lo añadimos al storage ```storage[position] = data```. Finalmente nos encargamos de avisar que hemos añadido un elemento, ```sem_empty.release()```.

Argumentos:
   - *storage* : array circular donde iremos guardando los elementos generados.
   - *data* : dato a insertar.
   - *position* : índice donde toca insertar el siguiente valor (en nuestro array circular).
   - *sem_capacity* : semáforo para controlar si el almacén está lleno.
   - *sem_empty* : semáforo para controlar si el almacén está vacío (servira para cuando el consumidor quiera acceder a nuestros datos).
  
```python
def add_data(storage, data, position, sem_capacity, sem_empty):
    try:
        # esperar a que tengamos espacio
        sem_capacity.acquire() 
        # añadir datos
        storage[position] = data 
        sem_empty.release()   
        delay(6)
    finally:  
        pass
```

## Consumidor <a name=id4></a>

Se encargar de ir consumiendo (de menor a mayor) los datos generados por los productores. Para ello utilizaremos tres funciones principales:


### consume <a name=id4.1></a>

Creamos el proceso del consumidor, el cual tendrá acceso a todos los storages y semáforos de los productores. Comenzamos el bucle para ir consumiendo todos los elementos:

 - Primero cogemos el primer valor de cada storage y los guardamos en una lista ```values```, con la función auxiliar **get_min_values** (esta se encargará de que los almacenes no esten vacíos).
 - Luego escogemos el elemento mínimo y nos guardamos su posición, ```index = np.argmin(values)```. 
 - Una vez sabemos el productor que a generado el valor mínimo (*index*) llamamos a la función **get_data** con los argumentos correctos, es decir, su storage, storge_index y sus semáforos respectivos (estos son los de la posición *index*). 
 - Finalmente sumamos una posición al Sumamos una posición al ```storages_index``` respectivo, ```storages_index[index] = (storages_index[index] + 1) % MAX_STORAGE```, esta es modular ya que es un array circular. Y guardamos los datos en nuestra lista resultado.
 
 Variables:
 
  - *final_list* : lista con los elementos finales (en orden).
  - *final_prods* : lista con los productores que han ido generando los elementos de la lista final (en orden).
  - *storages_index* : lista con las posiciones la cual nos toca consumir de cada uno de los storages de los productores. Al ser arrays circulares este índice es independiente del índice que guarda el productor para guardar el próximo elemento. 

```python
def consume(storages, sems_capacity, sems_empty):
    final_list  = []
    final_prods = []
    storages_index = [0 for _ in range(NPROD)] # índice donde coger el siguiente dato
    n = -1
     # coger el primer dato de cada productor
    values = get_min_values(storages, storages_index, sems_empty)
    while values != [np.inf for _ in range(NPROD)]:          
        n += 1
        # encontrar el elemento mínimo
        index = np.argmin(values)
        data = get_data(storages[index], storages_index[index], sems_capacity[index], sems_empty[index])
        storages_index[index] = (storages_index[index] + 1) % MAX_STORAGE
        # guardar datos
        final_list.append(data)
        final_prods.append(index)
        print (f"\n[{current_process().name}]\t<==\t| dato : {data}\t| posicion : {n}\t| producer : {index}")
        delay()
        # coger el primer dato de cada productor
        print (f"\n[{current_process().name}] buscando")
        values = get_min_values(storages, storages_index, sems_empty)
    # ver el resultado final
    print("\nLista final (ordenada con 'merge sort'):")
    print(final_list)
    print("\nPodemos observar de que productor viene cada elemento:")
    for n in range(N):
        print(f"[P{final_prods[n]}] {final_list[n]}")
```


### get_min_values <a name=id4.2></a>

Le pasamos todos los storages de los productores, ```storages```, y los índices respectivos donde toca "mirar" el elemento del storage, ```storages_index```. Primero aseguramos que todos los storages tengan al menos un elemento, para ello hacemos un bucle por todos los semaforos que indican si están vacíos, ```sems_empty```. Una vez pasado ese bucle podemos asegurar que todos los storages tienen al menos un elemento, por lo que creamos una lista con los elementos que tocan consumir. Además en la propia lista, si encontramos un -1, este indica que ese proceso a terminado, por lo que no queremos coger ese número. Como para escoger el número haremos un *min* ya que queremos el valor más pequeño, notaremos -1 como un infinito, ```np.inf```, para que este nunca sea escogido.

```python
def get_min_values(storages, storages_index, sems_empty):
    # esperar hasta que tengamos al menos un elemento en todos los storages
    for sem in sems_empty:
        sem.acquire()
        sem.release() 
    # coger valores mínimos : -1 indica que el proceso ha terminado
    g = lambda x : x if x != -1 else np.inf  
    values = [g(storage[i]) for storage, i in zip(storages, storages_index)]
    return values
```

### get_data <a name=id4.3></a>

Se encarga de coger el dato de un storage. Como argumentos le pasamos el storage concreto del que queremos coger el dato y la posición respectiva, por lo que no se encarga de ver si dicho dato es el mínimo o de si el almacen correspondiente está vacío, eso es prepocesado anteriormente. Únicamente cogemos el dato pedido de forma segura, es decir, avisamos de que hemos quuitado un elemento ```sem_empty.acquire()```, nos guardamos el elemento ```data = storage[position]```, lo vaciamos ```storage[position] = -2``` y finalmente indicamos al la capacidad del storge que tiene una posición libre ```sem_capacity.release()```.

```python
def get_data(storage, position, sem_capacity, sem_empty):
    try:
        sem_empty.acquire()     
        data = storage[position]
        storage[position] = -2  # dato vacío
        sem_capacity.release()  # vaciar un espacio
    finally:
        pass
    return data
```
