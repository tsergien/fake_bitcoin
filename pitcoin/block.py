#!/usr/bin/python3

import merkle
import hashlib
from serializer import Deserializer, Transaction
import json
from transaction import Transaction, CoinbaseTransaction

class Block():

    def __init__(self, timestamp, prev_hash, txs_list, nonce = 0):
        self.timestamp = timestamp
        self.nonce = nonce
        self.prev_hash = prev_hash
        self.txs = txs_list
        self.hash = self.calculate_hash()
        self.merkle = merkle.calculate(txs_list)

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
            sort_keys=True, indent=6)


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