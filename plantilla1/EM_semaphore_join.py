# -*- coding: utf-8 -*-
"""
Mutual exclusion problem solution with semaphores
"""
import time
import random

from multiprocessing import Process, BoundedSemaphore, current_process

N_non_critic = 5
N_critic = 5

def delay(factor=3):
    """ Just to propiciate interleaving """ 
    time.sleep(random.random()/factor)

def non_critic_section():
    p = current_process()
    for i in range(N_non_critic):
        print (p.name, "in non critic section", "(%i/%i)"%(i,N_non_critic))
        delay()

def critic_section():
    p = current_process()
    for i in range(N_critic):
        print (p.name, "in CRITIC section", "(%i/%i)"%(i,N_critic-1))
        delay()

def task(semaphore):
    non_critic_section()
    semaphore.acquire()
    critic_section()
    semaphore.release()


if __name__ == '__main__':    
    names = ["Ana","Eva","Pi","Pam","Pum"]
    jobs = []
    K = 1
    semaphore = BoundedSemaphore(K)
    for x in names:
        jobs.append(Process(target=task, name=x, args=(semaphore,)))
    for p in jobs:
        p.start()   
    for p in jobs:
        p.join()
    print('fin')
               
        
