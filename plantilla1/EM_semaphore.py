# -*- coding: utf-8 -*-
"""
Mutual exclusion problem solution with semaphores
"""
import time
import random

from multiprocessing import Process, BoundedSemaphore, \
    current_process, Value


def delay(factor=6):
    """ Just to propiciate interleaving """
    time.sleep(random.random()/factor)

def non_critic_section():
    p = current_process()
    print (f"{p.name} in non critic section")
    delay()

def critic_section(c):
    p = current_process()
    print (f"{p.name} in CRITIC section: {c.value}")
    temp = c.value + 1
    delay()
    c.value = temp
    print (f"{p.name} in finishing CRITIC section: {c.value}")

def task(semaphore, c):
    for i in range(100):
        non_critic_section()
        semaphore.acquire()
        critic_section(c)
        semaphore.release()


if __name__ == '__main__':
    names = ["Ana","Eva","Pi","Pam","Pum"]
    jobs = []
    K = 1
    c = Value('i', 0)
    semaphore = BoundedSemaphore(K)
    for x in names:
        jobs.append(Process(target=task, name=x, args=(semaphore,c)))
    for p in jobs:
        p.start()
    for p in jobs:
        p.join()
    print(f"The End....{c.value}")
