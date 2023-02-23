from multiprocessing import Process, Manager, Semaphore, BoundedSemaphore
from multiprocessing import current_process

from time import sleep
from random import random

N = 10
K = 3

def p(almacen, sem):
    for v in range(N,2*N):
        print (current_process().name, "produciendo")
        sleep(random()/3)
        almacen.append(v)
        print (current_process().name, "producido", v)
        sem.release()

def c(almacen, sem):
    pos = 0
    for v in range(N):
        print (current_process().name, "desalmacenando")
        sem.acquire()
        dato = almacen[pos]
        pos += 1
        print (current_process().name, "consumiendo", dato)
        sleep(random()/3)


def main():
    manager = Manager()
    almacen = manager.list()
    sem = BoundedSemaphore(0)

    productor = Process(target=p, name="productor", args=(almacen, sem))
    consumidor = Process(target=c, name="consumidor", args=(almacen, sem))

    productor.start()
    #sleep(1) # esto produce un error, hay que usar semáforos generales
    consumidor.start()
    consumidor.join()
    productor.join()

if __name__ == "__main__":
    main()
