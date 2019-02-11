#!/usr/bin/python3

import merkle
import hashlib
from serializer import Deserializer, Transaction
import json
from transaction import Transaction, CoinbaseTransaction

max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

class Block():

    def __init__(self, timestamp, prev_hash, txs_list, nonce = 0):
        self.timestamp = timestamp
        self.nonce = nonce
        self.prev_hash = prev_hash
        self.txs = txs_list
        self.hash = self.calculate_hash()
        self.merkle = merkle.calculate(txs_list)
        self.bits = 0x1903a30c
        self.difficulty = self.count_difficulty()

    def calculate_hash(self):
        s = str(self.timestamp) + str(self.prev_hash) + str(self.txs) + str(self.nonce)
        return hashlib.sha256(bytes(s, "utf-8")).hexdigest()

    def tx_validator(self):
        for t in self.txs:
            Deserializer().deserialize(t)
        return True

    def mine(self, complexity):
        while self.hash[:complexity] != "0" * complexity:
            self.nonce = self.nonce + 1
            self.hash = self.calculate_hash()
        print("Congratulations! Block " + self.toJSON() + " was mined!")
        return self

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=8)


    def count_target(self):
        exp = self.bits >> 24
        mant = self.bits & 0xffffff
        target = mant * (1 << (8 * (exp - 3)))
        return target
    
    def count_difficulty(self):
        self.difficulty = max_target / self.count_target()
        return self.difficulty



def block_from_JSON(id):
    try:
        db = TinyDB('blks.json')
        table = db.table('chain')
        data = table.get(doc_id=id)
        block = Block(data['t'], data['nonce'], data['prev_hash'], data['txs'])
        block.hash = data['hash']
        block.merkle = data['merkle']
        return block
    except:
        print("No " + str(id) + " in the blockchain.")