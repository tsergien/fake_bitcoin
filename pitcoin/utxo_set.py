#!/usr/bin/python3

from transaction import Transaction, Output, Input, CoinbaseTransaction, output_json_decoder
from tinydb import TinyDB, Query
from serializer import Serializer, Deserializer
from hashlib import sha256
from tinydb import TinyDB, Query
from wallet import pubkey_hash_to_address

class OutPoint():
    def __init__(self, vout, txid, output):
        self.vout = vout
        self.txid = txid
        self.output = output

class Utxos():

    def __init__(self):
        self.utxo_db = TinyDB('utxo.json')
        self.pool = {} # dict { 'hash' : output_class_object }
        self.update_pool([])

    def update_pool(self, txs):
        for serial_tx in txs:
            tx = Deserializer().deserialize(serial_tx)
            for j in range(tx.inp_counter):
                query_hash = Query()
                res_q = self.utxo_db.search(query_hash.hash == '{:8x}'.format(tx.inputs[j].vout) + tx.inputs[j].txid)
                if res_q:
                    self.utxo_db.remove(query_hash.hash == '{:8x}'.format(tx.inputs[j].vout) + tx.inputs[j].txid)
            for i in range(tx.outp_counter):
                hash = sha256( sha256( bytes(Serializer().serialize(tx), "utf-8" ) ).digest() ).hexdigest()
                self.utxo_db.insert({'hash': '{:8x}'.format(i) + hash,\
                     'output': tx.outputs[i].toJSON()})
        
        db_len = len(self.utxo_db)
        db_list = self.utxo_db.all()
        for i in range(0, db_len):
            outp_json = db_list[i]
            self.pool[ outp_json['hash'] ] = output_json_decoder(outp_json['output'])


    def get_outputs_to_spend(self, sender, amount):
        utxos_to_spend = []
        utxos_amount = 0
        for key in self.pool:
            if sender == pubkey_hash_to_address(self.pool[key].scriptPubKey[6:-4]):
                txid = key[8:]
                vout = key[:8]
                nVal = self.pool[key].nVal
                recipient = pubkey_hash_to_address(self.pool[key].scriptPubKey[6:-4])
                utxos_to_spend.append(OutPoint(vout, txid, Output(nVal, recipient)))
                utxos_amount += self.pool[key].nVal
                if utxos_amount > amount:
                    break
        return utxos_to_spend

    def get_balance(self, address):
        bal = 0
        for key in self.pool:
            if address == pubkey_hash_to_address(self.pool[key].scriptPubKey[6:-4]):
                bal += self.pool[key].nVal
        return bal

