from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
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
    - ADD_DATA -> ADD DATA TO THE STORAGE.
    - PRODUCE  -> GENERATES NEW DATA AND ADD IT TO THE STORAGE.
"""
def add_data(storage, data, position, access_lock, capacity_lock, empty_lock):
    access_lock.acquire()
    pos = position.value
    try:
        storage[pos] = data
        position.value = pos + 1
        capacity_lock.acquire()  
        empty_lock.release()     
        delay(6)
    finally:
        access_lock.release()

def produce(storage, position, access_lock, capacity_lock, empty_lock): 
    last_data = 0
    for n in range(K+1):
        # create new data
        print (f"\n[{current_process().name}] produciendo")
        data = last_data + random.randint(1,10) if n < K else -1 # end of secuence 
        # wait until we have space in our storage
        capacity_lock.acquire()
        capacity_lock.release()
        # add data
        add_data(storage, data, position, access_lock, capacity_lock, empty_lock)
        print (f"\n[{current_process().name}]\t==>\t| dato : {data}\t| pos : {position.value-1}")
        last_data = data


"""
    CONSUMER:
    - GET_DATA            -> GET DATA FROM ONE OF THE STORAGES AND ADD IT TO THE FINAL LIST.
    - GET_MIN_VALUE_INDEX -> FIND THE STORAGE WHO HAS THE MINIMUM ELEMENT (KNOWING THAT ALL OF THEM ARE NOT EMPTY OR FULL & CHECKS IF IT IS FINISHED "-1").
    - CONSUME             -> WAITS UNTIL EVERY STORAGE HAS AT LEATS ONE ELEMENT. THEN CONSUME THE MINIMUM ELEMENT TO ADD IT TO THE FINAL LIST. 
"""
def get_data(storage, position, access_lock, capacity_lock, empty_lock):
    access_lock.acquire()
    pos = position.value
    try:
        data = storage[0]
        position.value = pos - 1
        # (if) the storage only had one element => now is empty
        empty_lock.acquire() 
        # (if) the storage was full => now we can release one position
        capacity_lock.release()  
        for i in range(pos-1):
            storage[i] = storage[i+1]
        storage[pos-1] = -2  # empty
    finally:
        access_lock.release()
    return data

def get_min_value_index(storages):
    g = lambda x : x if x != -1 else np.inf  # if x == -1 then that storage is finished so we dont want to select it
    values = [g(storage[0]) for storage in storages]
    return np.argmin(values)

def consume(final_list, storages, storages_last_index, storages_access, storages_capacity, storages_empty):
    for n in range(N):
        # wait until we have at least one element in every storage
        for sem in storages_empty:
            sem.acquire()           
        # realese their locks after it
        for sem in storages_empty:
            sem.release()           
        # find the minimun value and consume it (of the non finished storages)
        print (f"\n[{current_process().name}] desalmacenando")
        index = get_min_value_index(storages)
        data = get_data(storages[index], storages_last_index[index], storages_access[index], storages_capacity[index], storages_empty[index])
        # save data
        final_list[2*n] = index
        final_list[2*n+1] = data
        print (f"\n[{current_process().name}]\t==>\t| dato : {data}\t| pos : {n}")
        delay()


"""
    MAIN FUNCTION:
    - CREATE 'NPROD' PRODUCERS, EACH OF THEM PRODUCE 'K' VALUES AND AT THE END WE RETURN THE FINAL_LIST WITH ALL THESE VALUES SORTED.  
    EVERY PRODUCER HAS HIS OWN STORAGE OF A MAXIMUM OF 'MAX_STORAGE' ELEMENTS. SO IF WE RUN OUT OF SPACE WE WAIT UNTIL THE CONSUMER CONSUME SOME OF
    OUR ELEMENTS.
"""
def main():

    final_list = Array('i', 2*N)  # process index -> 2*n / value -> 2*n+1
    for i in range(2*N):
        final_list[i] = 0

    # individual storage for every producer (default / empty value : -2)
    storages = [Array('i', MAX_STORAGE) for _ in range(NPROD)]
    for s in storages:
        for i in range(MAX_STORAGE):
            s[i] = -2

    # position of the last element (+1) of every storage (the index in which is going to be the next element) : shared variable
    storages_last_index = [Value('i', 0) for _ in range(NPROD)]

    # Semaphores : 
    storages_access   = [Lock() for _ in range(NPROD)]                   # only one (producer[i] / consumer) can access to the storage[i]
    storages_capacity = [BoundedSemaphore(NPROD) for _ in range(NPROD)]  # blocks when the storage is full & (if is blocked) release when we take of one element
    storages_empty    = [Semaphore(0) for _ in range(NPROD)]             # blocks when is empty (by default) & and release when we have at least one element


    # NPROD producers -> each of them are going to create K values (in order)
    producers = [ Process(target=produce,
                        name=f'Prod - {index+1}',
                        args=(storages[index], storages_last_index[index], storages_access[index], storages_capacity[index], storages_empty[index]))
                for index in range(NPROD) ]

    # A individual consumer, who is going to be consumin one element every time
    # when the 'NPROD' producers has at least one value available 
    consumer = Process(target=consume,
                       name=f"Consumer",
                       args=(final_list, storages, storages_last_index, storages_access, storages_capacity, storages_empty))

    # start all the Process and join them
    for p in producers + [consumer]:
        p.start()
    for p in producers + [consumer]:
        p.join()

    # see the final results
    print("\nFinal merge list:")
    for n in range(N):
        print(f"[P{final_list[2*n]}] {final_list[2*n+1]}")


if __name__ == '__main__':
    main()
