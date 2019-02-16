#!/usr/bin/python3

import merkle
import hashlib
from serializer import Deserializer, Transaction
import json
import time
import struct
from transaction import Transaction, CoinbaseTransaction

max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

class Block():

    def __init__(self, timestamp, prev_hash, txs_list, nonce = 0):
        self.version = 1
        self.timestamp = timestamp
        self.nonce = nonce
        self.prev_hash = prev_hash
        self.txs = txs_list
        self.merkle = merkle.calculate(txs_list)
        self.bits = 0x10001000
        self.difficulty = self.count_difficulty()
        self.height = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        print("\n\n" + str(type(self.timestamp)))
        s = struct.pack("<L", self.version) + bytes(str(self.prev_hash), 'utf-8') + \
            bytes(str(self.merkle), 'utf-8') + struct.pack("<L", self.timestamp) 
            # bytes(hex(count_target(self.bits)), 'utf-8') + struct.pack("<L", self.nonce)
        return hashlib.sha256(s).hexdigest()

    def tx_validator(self):
        for t in self.txs:
            Deserializer().deserialize(t)
        return True

    def mine(self, bits):
        self.bits = bits
        target = count_target(bits)
        while int(self.hash, 16) >= target:
            self.nonce = self.nonce + 1
            self.hash = self.calculate_hash()
        return self

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=10)

    
    def count_difficulty(self):
        self.difficulty = max_target / count_target(self.bits)
        return self.difficulty


def count_target(bits):
    exp = bits >> 24
    mant = bits & 0xffffff
    target = mant * (1 << (8 * (exp - 3)))
    return target

def block_from_JSON(id):
    try:
        db = TinyDB('blks.json')
        table = db.table('chain')
        data = table.get(doc_id=id)
        block = Block(data['t'], data['prev_hash'], data['txs'], data['nonce'])
        block.hash = data['hash']
        block.merkle = data['merkle']
        block.difficulty = data['difficulty']
        block.height = data['height']
        block.bits = data['bits']
        return block
    except:
        print("No " + str(id) + " in the blockchain.")