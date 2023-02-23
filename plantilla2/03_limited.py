from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random


N = 100
K = 10
NPROD = 3
NCONS = 3

def delay(factor = 3):
    sleep(random()/factor)


def add_data(storage, index, pid, data, mutex):
    mutex.acquire()
    try:
        storage[index.value] = pid*1000 + data
        delay(6)
        index.value = index.value + 1
    finally:
        mutex.release()


def get_data(storage, index, mutex):
    mutex.acquire()
    try:
        data = storage[0]
        index.value = index.value - 1
        delay()
        for i in range(index.value):
            storage[i] = storage[i + 1]
        storage[index.value] = -1
    finally:
        mutex.release()
    return data


def producer(storage, index, empty, non_empty, mutex):
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty.acquire()
        add_data(storage, index, int(current_process().name.split('_')[1]),
                 v, mutex)
        non_empty.release()
        print (f"producer {current_process().name} almacenado {v}")


def consumer(storage, index, empty, non_empty, mutex):
    for v in range(N):
        non_empty.acquire()
        print (f"consumer {current_process().name} desalmacenando")
        dato =get_data(storage, index, mutex)
        empty.release()
        print (f"consumer {current_process().name} consumiendo {dato}")
        delay()

def main():
    storage = Array('i', K)
    index = Value('i', 0)
    for i in range(K):
        storage[i] = -1
    print ("almacen inicial", storage[:], "indice", index.value)

    non_empty = Semaphore(0)
    empty = BoundedSemaphore(K)
    mutex = Lock()

    prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage, index, empty, non_empty, mutex))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                      name=f"cons_{i}",
                      args=(storage, index, empty, non_empty, mutex))
                for i in range(NCONS) ]

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()


if __name__ == '__main__':
    main()
