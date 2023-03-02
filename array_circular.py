from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore
from multiprocessing import current_process
from multiprocessing import Array
from time import sleep
import random
import numpy as np




K = 10              # number of elements (to produce) per producer
MAX_STORAGE = 5     # max capacity of a storage
NPROD = 3           # number of producers
N = K * NPROD       # total number of values in the final list (K values per producer)


def delay(factor = 3):
    sleep(random.random()/factor)


"""
    PRODUCER:
    ---------
    - ADD_DATA -> ADD DATA TO THE STORAGE.
    - PRODUCE  -> GENERATES NEW DATA.
"""
def add_data(storage, data, position, sem_capacity, sem_empty):
    try:
        # wait until we have space
        sem_capacity.acquire() 
        # add data
        storage[position] = data 
        sem_empty.release()   
        delay(6)
    finally:  
        pass

def produce(storage, sem_capacity, sem_empty): 
    last_data = 0
    position = 0   # index to insert the next value
    for n in range(K+1):
        # create new data
        print (f"\n[{current_process().name}] produciendo")
        data = last_data + random.randint(1,10) if n < K else -1 # end of secuence 
        # add data
        add_data(storage, data, position, sem_capacity, sem_empty)
        print (f"\n[{current_process().name}]\t==>\t| dato : {data}\t| posicion : {position}")
        position = (position + 1) % MAX_STORAGE
        last_data = data


"""
    CONSUMER:
    ---------
    - GET_DATA       -> GET DATA FROM ONE OF THE STORAGES.
    - GET_MIN_VALUES -> RETURN A LIST OF THE FIRST ELEMENT OF EVERY STORAGE.
    - CONSUME        -> TAKE THE MINIMUM ELEMENT AND ADD IT TO THE FINAL LIST. 
"""
def get_data(storage, position, sem_capacity, sem_empty):
    try:
        data = storage[position]
        sem_empty.acquire()     # 
        sem_capacity.release()  # release space
        storage[position] = -2  # empty
    finally:
        pass
    return data

def get_min_values(storages, storages_index, sems_empty):
    # wait until we have at least one element in every storage
    for sem in sems_empty:
        sem.acquire()
        sem.release() 
    # get min values : -1 indicates that the process is finished
    g = lambda x : x if x != -1 else np.inf  
    values = [g(storage[i]) for storage, i in zip(storages, storages_index)]
    return values

def consume(storages, sems_capacity, sems_empty):
    final_list  = []
    final_prods = []
    storages_index = [0 for _ in range(NPROD)] # index to take the next value
    n = -1
    while True:          
        n += 1
        # get the first value of every producer
        print (f"\n[{current_process().name}] buscando")
        values = get_min_values(storages, storages_index, sems_empty)
        # check if we have finished
        if values == [np.inf for _ in range(NPROD)]:
            break
        # find the min value
        index = np.argmin(values)
        data = get_data(storages[index], storages_index[index], sems_capacity[index], sems_empty[index])
        storages_index[index] = (storages_index[index] + 1) % MAX_STORAGE
        # save data
        final_list.append(data)
        final_prods.append(index)
        print (f"\n[{current_process().name}]\t<==\t| dato : {data}\t| posicion : {n}\t| producer : {index}")
        delay()
    # see the final results
    print("\nLista final (ordenada con 'merge sort'):")
    print(final_list)
    print("\nPodemos observar de que productor viene cada elemento:")
    for n in range(N):
        print(f"[P{final_prods[n]}] {final_list[n]}")


"""
    MAIN FUNCTION:
    - CREATE 'NPROD' PRODUCERS, EACH OF THEM PRODUCE 'K' VALUES AND AT THE END WE RETURN THE FINAL_LIST WITH ALL THESE VALUES SORTED.  
    EVERY PRODUCER HAS HIS OWN STORAGE OF A MAXIMUM OF 'MAX_STORAGE' ELEMENTS. SO IF WE RUN OUT OF SPACE WE WAIT UNTIL THE CONSUMER 
    TAKES SOME OF OUR ELEMENTS.
"""
def main():

    # individual storage for every producer (default / empty value : -2)
    storages = [Array('i', MAX_STORAGE) for _ in range(NPROD)]
    for s in storages:
        for i in range(MAX_STORAGE):
            s[i] = -2

    # Semaphores : 
    sems_capacity = [BoundedSemaphore(NPROD) for _ in range(NPROD)]  # blocks (the producer) when the storage is full
    sems_empty    = [Semaphore(0) for _ in range(NPROD)]             # blocks (the consumer) when the storage is empty


    # NPROD producers -> each of them are going to create K values (in order)
    producers = [ Process(target=produce,
                        name='Prod' + (' '*3 + str(index))[-4:],
                        args=(storages[index], sems_capacity[index], sems_empty[index]))
                for index in range(NPROD) ]

    # 1 consumer : takes all the elements of the producers in order 
    consumer = Process(target=consume,
                       name=f"Consumer",
                       args=(storages, sems_capacity, sems_empty))

    # start all the Process and join them
    for p in producers + [consumer]:
        p.start()
    for p in producers + [consumer]:
        p.join()


if __name__ == '__main__':
    main()
