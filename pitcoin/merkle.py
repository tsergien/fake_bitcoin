#!/usr/bin/python3

import hashlib
from transaction import Transaction, CoinbaseTransaction
from binascii import unhexlify

def calculate(txs_list:list):
    l = len(txs_list)
    txsc = txs_list[:]
    if l % 2 == 1:
        txsc.append(txsc[l - 1])
        l += 1
    hashes = []
    for i in range(l):
        hashes.append( hashlib.sha256(bytes(txsc[i], "utf-8")).hexdigest() )
    next_level = []
    while l > 1:
        i = 0
        while i+1 < l:
            next_level.append( hashlib.sha256( bytes(hashes[i] + hashes[i + 1], "utf-8")).hexdigest() )
            i = i + 2
        hashes = next_level
        next_level = []
        l = len(hashes)
    return hashes[0]



