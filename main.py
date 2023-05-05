from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore
from multiprocessing import current_process
from multiprocessing import Array
from time import sleep
import random
import numpy as np




K = 10              # nº de elemtos a producir (por productor)
MAX_STORAGE = 5     # capacidad máxima del storage
NPROD = 3           # nº de productores
N = K * NPROD       # nº total de elemntos (a introducir en la lista final)


def delay(factor = 3):
    sleep(random.random()/factor)


"""
    PRODUCTOR:
    ---------
    - ADD_DATA -> AÑADE DATOS AL STORAGE.
    - PRODUCE  -> GENERA NUEVOS DATOS.
"""
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


"""
    CONSUMIDOR:
    ---------
    - GET_DATA       -> COGER DATO DE UNO DE LOS STORAGES
    - GET_MIN_VALUES -> RETORNAR UNA LISTA DE LOS PRIMEROS ELEMENTOS DE LOS STORAGES
    - CONSUME        -> COGER EL MIN ELEMENTO Y AÑADIRLO A LA LISTA FINAL
"""
def get_data(storage, position, sem_capacity, sem_empty):
    try:
        sem_empty.acquire()     
        data = storage[position]
        storage[position] = -2  # dato vacío
        sem_capacity.release()  # vaciar un espacio
    finally:
        pass
    return data

def get_min_values(storages, storages_index, sems_empty):
    # esperar hasta que tengamos al menos un elemento en todos los storages
    for sem in sems_empty:
        sem.acquire()
        sem.release() 
    # coger valores mínimos : -1 indica que el proceso ha terminado
    g = lambda x : x if x != -1 else np.inf  
    values = [g(storage[i]) for storage, i in zip(storages, storages_index)]
    return values

def consume(storages, sems_capacity, sems_empty):
    final_list  = []
    final_prods = []
    storages_index = [0 for _ in range(NPROD)] # índice donde coger el siguiente dato
    n = -1
    # coger el primer dato de cada productor
    print (f"\n[{current_process().name}] buscando")
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


"""
    MAIN:
    -----
    - CREA 'NPROD' PRODUCTORES, CADA UNO PRODUCE 'K' VALORES Y AL FINAL RETORNAMOS LA LISTA FINAL CON TODOS LOS VALORES ORDENADOS.  
    TODOS LOS PRODUCTORES TIENEN SU PROPIO STORAGE DE CAPACIDAD MÁXIMA: 'MAX_STORAGE'. POR LO QUE SI NOS QUEDAMOS SIN ESPACIO EN EL 
    STORAGE ESPERAREMOS A QUE EL CONSUMIDOR NOS QUITE ALGÚN ELEMENTO.
"""
def main():

    # storage individual para cada productor (valor nulo : -2)
    storages = [Array('i', MAX_STORAGE) for _ in range(NPROD)]
    for s in storages:
        for i in range(MAX_STORAGE):
            s[i] = -2

    # Semaforos : 
    sems_capacity = [BoundedSemaphore(MAX_STORAGE) for _ in range(NPROD)]  # bloquea (el productor) cuando el storage esta lleno
    sems_empty    = [Semaphore(0) for _ in range(NPROD)]             # bloquea (el consumidor) cuando el storage esta vacío


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


if __name__ == '__main__':
    main()
