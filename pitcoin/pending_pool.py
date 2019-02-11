#!/usr/bin/python3

from serializer import Deserializer
from transaction import Transaction

def get_tx(tx_str):
    Deserializer().deserialize(tx_str)
    save_to_mempool(tx_str)
    return get_last3()

def save_to_mempool(tx_str):
    open("mempool.dat", "a+").write(tx_str + "\n")

def get_last3()->list:
    txs = []
    try:
        array = []
        with open("mempool.dat", "r") as f:
            array = f.read().splitlines()
        ind = len(array) - 1
        m = min(len(array), 3)
        for i in range(0, m):
            if ind - i < 0:
                break
            txs.append(array[ind - i].replace('\n', ''))
    except:
        pass
    return txs

def get_first3()->list:
    txs = []
    try:
        array = []
        with open("mempool.dat", "r") as f:
            array = f.read().splitlines()
        m = min(len(array), 3)
        for i in range(0, m):
            txs.append(array[i].replace('\n', ''))
        f.close()
        open("mempool.dat", "w").close()
        w = open("mempool.dat", "a+")
        l = len(array)
        for i in range(m, l):
            w.write(array[i] + "\n")
        w.close()
    except:
        pass
    return txs

