from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
import random
import numpy as np


# release -> +1
# acquire -> -1


K = 10         # number of elements (to produce) per producer
NPROD = 3      # number of producers
N = K * NPROD  # total number of values in the final list (K values per producer)


def delay(factor = 3):
    sleep(random.random()/factor)


"""
    PRODUCE - ADD DATA TO THW STORAGE
"""
def add_data(storage, index, i, data, storage_lock):
    storage_lock[index].acquire()
    try:
        storage[index][i] = data
        delay(6)
    finally:
        storage_lock[index].release()


def produce(storage, index, storage_lock):
    last_data = 0
    for i in range(K):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        data = last_data + random.randint(1,10)
        add_data(storage, index, i, data, storage_lock)
        print (f"producer {current_process().name} almacenado {data}")
        last_data = data

"""
    CONSUME - ADD DATA TO THE FINAL ARRAY (final_list)
"""
def get_data(storage, index, storage_first_index, storage_lock):
    storage_lock[index].acquire()
    try:
        data = storage[index][storage_first_index[index]]
        storage_first_index[index] += 1
        delay()
        # for i in range(index.value):
        #     storage[i] = storage[i + 1]
        # storage[index.value] = -1
    finally:
        storage_lock[index].release()
    return data


def get_first_value(storage, storage_first_index, index):
    i = storage_first_index[index]
    if i == K:
        return np.inf
    return storage[index][i]


def consume(final_list, storage, storage_first_index, storage_lock):
    for n in range(N):
        # wait until we have at least one element in every storage
        # take care of the producers that dont have any data left (== K)
        access = np.array([(storage_first_index[i] == K) for i in range(NPROD)])  
        while not access.all():
            for index in range(NPROD):
                if not access[index]:
                    i = storage_first_index[index]
                    access[index] = (storage[index][i] != -2)
            delay(6)
        # find the minimun value and consume it (of the non empty storages)
        print (f"consumer desalmacenando el {n}-esimo")
        index = np.argmin([get_first_value(storage, storage_first_index, index) for index in range(NPROD)])
        data = get_data(storage, index, storage_first_index, storage_lock)
        final_list[n] = data
        print (f"consumer consumiendo {data}")
        delay()


def main():

    # final list (default values : -1)
    final_list = Array('i', N)
    for i in range(N):
        final_list[i] = -1
    print ("Empty list:")
    print(final_list[:])

    # individual storage for every producer (default / empty value : -2)
    storage = [Array('i', K) for _ in range(NPROD)]
    for s in storage:
        for i in range(K):
            s[i] = -2

    # index of the first element of every storage : shared variable
    storage_first_index = Array('i', NPROD)
    for i in range(NPROD):
        storage_first_index[i] = 0

    # Semaphores : only one (producer[i] / consumer) can access to the storage[i], for i = 1, ..., NPROD.
    storage_lock = [Lock() for _ in range(NPROD)]  

    # NPROD producers -> each of them are going to create K values (in order)
    producers = [ Process(target=produce,
                        name=f'prod_{index}',
                        args=(storage, index, storage_lock))
                for index in range(NPROD) ]

    # A individual consumer, who is going to be consumin one element every time
    # the NPROD producers has at least one value available 
    consumer = Process(target=consume,
                       name=f"consumer",
                       args=(final_list, storage, storage_first_index, storage_lock))

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