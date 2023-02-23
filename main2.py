from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
import random
import numpy as np


# release -> +1
# acquire -> -1


K = 10              # number of elements (to produce) per producer
MAX_STORAGE = 5     # max capacity of a storage
NPROD = 3           # number of producers
N = K * NPROD       # total number of values in the final list (K values per producer)


def delay(factor = 3):
    sleep(random.random()/factor)


"""
    PRODUCE - ADD DATA TO THE STORAGE
"""
def add_data(storage, index, data, storage_last_index, storage_lock):
    storage_lock[index].acquire()
    try:
        storage[index][storage_last_index[index]] = data
        storage_last_index[index] += 1
        delay(6)
    finally:
        storage_lock[index].release()


def produce(storage, index, storage_last_index, storage_lock):
    last_data = 0
    for n in range(K+1):
        # create new data
        print (f"[{current_process().name}] produciendo")
        data = last_data + random.randint(1,10) if n < K else -1 # end of secuence 
        # wait until we have space in our storage
        while storage_last_index[index] == MAX_STORAGE:
            delay(6)
        # add data
        add_data(storage, index, data, storage_last_index, storage_lock)
        print (f"[{current_process().name}]\t==>\t| dato : {data}\t| pos : {storage_last_index[index]-1}")
        last_data = data

"""
    CONSUME - ADD DATA TO THE FINAL ARRAY (final_list)
"""
def get_data(storage, index, storage_last_index, storage_lock):
    storage_lock[index].acquire()
    try:
        data = storage[index][0]
        storage_last_index[index] -= 1
        delay()
        for i in range(storage_last_index[index]):
            storage[index][i] = storage[index][i+1]
        storage[index][storage_last_index[index]] = -2  # empty
    finally:
        storage_lock[index].release()
    return data


def get_min_value_index(storage):
    g = lambda x : x if x != -1 else np.inf  # if x == -1 then that storage is finished so we dont want to select it
    values = [g(storage[index][0]) for index in range(NPROD)]
    return np.argmin(values)


def consume(final_list, storage, storage_last_index, storage_lock):
    for n in range(N):
        # wait until we have at least one element in every storage
        # take care of the producers that dont have any data left (== K)
        access = np.array([(storage[index][0] != -2) for index in range(NPROD)])  
        while not access.all():
            for index in range(NPROD):
                if not access[index]:
                    access[index] = (storage[index][0] != -2)
            delay(6)
        # find the minimun value and consume it (of the non empty storages)
        print (f"[{current_process().name}] desalmacenando")
        index = get_min_value_index(storage)
        data = get_data(storage, index, storage_last_index, storage_lock)
        final_list[n] = data
        print (f"\n[{current_process().name}]\t==>\t| dato : {data}\t| pos : {n}")
        delay()




def main():

    # final list (default values : -1)
    final_list = Array('i', N)
    for i in range(N):
        final_list[i] = -1
    print ("Empty list:")
    print(final_list[:])

    # individual storage for every producer (default / empty value : -2)
    storage = [Array('i', MAX_STORAGE) for _ in range(NPROD)]
    for s in storage:
        for i in range(MAX_STORAGE):
            s[i] = -2

    # position of the last element (+1) of every storage (the index in which is going to be the next element) : shared variable
    storage_last_index = Array('i', NPROD)
    for i in range(NPROD):
        storage_last_index[i] = 0

    # Semaphores : only one (producer[i] / consumer) can access to the storage[i], for i = 1, ..., NPROD.
    storage_lock = [Lock() for _ in range(NPROD)]  

    # NPROD producers -> each of them are going to create K values (in order)
    producers = [ Process(target=produce,
                        name=f'Prod - {index+1}',
                        args=(storage, index, storage_last_index, storage_lock))
                for index in range(NPROD) ]

    # A individual consumer, who is going to be consumin one element every time
    # the NPROD producers has at least one value available 
    consumer = Process(target=consume,
                       name=f"Consumer",
                       args=(final_list, storage, storage_last_index, storage_lock))

    # start all the Process and join them
    for p in producers + [consumer]:
        p.start()
    for p in producers + [consumer]:
        p.join()

    # see the final results
    print("Final merge list:")
    print(final_list[:])


if __name__ == '__main__':
    main()