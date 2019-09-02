#!/usr/bin/env python3

from transaction import Transaction, CoinbaseTransaction, Output
from block import Block, block_from_JSON, count_target, max_target
from serializer import Serializer
import time
import pending_pool
from hashlib import sha256
from tinydb import TinyDB, Query
import requests
import merkle
import script
import wallet
from utxo_set import Utxos
import re
import math
from form_tx import form_coinbase, form_transaction
import time

max_time = 10 # 2 weeks
min_time = 1 # half of a week
g_miner_reward = 5000
first_prev_txid = "00000000000000000000000000000000000000000000000000000000000000"

class Blockchain():

    def __init__(self):
        self.db = TinyDB('blks.json')
        self.utxo_pool = Utxos()
        self.utxo_pool.update_pool([])##############################
        self.bits = 0x22222222
        try:
            with open("miner_key", "r")as f:
                self.miner_wif = f.read(51)
            with open("miner_address.txt", "r") as f2:
                self.address = f2.read(34)
        except:
            with open("miner_key", "w") as f:
                privkey = wallet.gen_privkey()
                self.miner_wif = wallet.privkey_to_wif(privkey)
                f.write( self.miner_wif  + "\n")
            with open("miner_address.txt", "w") as f2:
                self.address = wallet.gen_address(wallet.get_pubkey_str(privkey))
                f2.write(self.address + "\n")


    def mine(self):
        if self.height() == 0:
            return self.genesis_block()
        coinbase_tx = form_coinbase(self.address, self.miner_wif, self.get_current_reward())
        serialized_cb = Serializer().serialize(coinbase_tx)
        txs = pending_pool.get_first3()
        txs.insert(0, serialized_cb)
        b = Block(time.time(), self.prev_hash(), txs, 0, self.bits).mine()
        b.height = self.height()
        print("Congratulations! Block " + b.toJSON() + " was mined!")
        self.db.insert({
                'Block Size': 0xffffffff,
                'Version': 1,
                'Previous Block Hash': b.prev_hash,
                'Merkle Root': b.merkle,
                'Timestamp': int(b.timestamp),
                'Difficulty Target': hex(b.bits),
                'Nonce': b.nonce,
                'Transaction Counter': len(b.txs),
                'Transactions': b.txs
                })
        # if self.height() % 5 == 0:
        #     self.recalculate_bits()
        self.utxo_pool.update_pool(txs)

    def genesis_block(self):
        serialized_cb = Serializer().serialize( form_coinbase(self.address, self.miner_wif, self.get_current_reward()) )
        txs = [serialized_cb]
        b = Block(time.time(), first_prev_txid, txs, 0,  self.bits).mine()
        print("Congratulations! Block " + b.toJSON() + " was mined!")
        self.db.insert({
                'Block Size': 0xffffffff,
                'Version': 1,
                'Previous Block Hash': b.prev_hash,
                'Merkle Root': b.merkle,
                'Timestamp': int(b.timestamp),
                'Difficulty Target': hex(b.bits),
                'Nonce': b.nonce,
                'Transaction Counter': len(b.txs),
                'Transactions': b.txs
                })
        self.utxo_pool.update_pool(txs)


    def resolve_conflicts(self):
        nodes_list = self.get_nodes_list()
        if len(nodes_list) == 0:
            print("There are no nodes in the list")
            return
        longest_chain_url = nodes_list[0]
        longest_length = 0
        for node in nodes_list:
            cur_len = requests.get("http://" + node + "/chain/length")
            cur_len = int(cur_len.json())
            if longest_length < cur_len:
                longest_chain_url = node
                longest_length = cur_len
        chain = requests.get("http://" + longest_chain_url + "/chain").json()
        if self.height() < longest_length: #check
            open("blks.json", "w").close()
            open("utxo.json", "w").close()
            for c in chain:
                print("BLOCK----> " + str(c))
                self.db.insert(c)
                self.utxo_pool.update_pool(c['Transactions'])


    def recalculate_bits(self):
        diff_time = self.db.all()[-1]['Timestamp'] - self.db.all()[-5]['Timestamp']
        if diff_time > max_time:
            diff_time = max_time
        elif diff_time < min_time:
            diff_time = min_time
        curr_bits = int(self.db.all()[-1]['Difficulty Target'], 16)
        new_target = (diff_time * count_target(curr_bits)) // max_time
        if new_target > max_target:
            new_target = max_target
        self.bits = to_bitsn(new_target)
        print("New bits: " + str(self.bits))


    def is_valid_chain(self):
        prev = block_from_JSON(1)
        if prev.hash != prev.calculate_hash() \
            or prev.merkle != merkle.calculate(prev):
            return False
        for i in range(2, self.height() + 1):
            blk = block_from_JSON(i)
            if blk.hash != blk.calculate_hash() \
            or blk.merkle != merkle.calculate(blk) \
            or blk.prev_hash != prev.hash:
                return False
        return True

    def get_nodes_list(self):
        try:
            f = open("nodes.txt", "r")
            lines = f.readlines()
            nodes = []
            for l in lines:
                nodes.append(l.replace("\n", ""))
            f.close()
            return nodes
        except:
            return []

    def add_node(self, ip):
        if not re.match(r'(\d{1,3}\.){3}\d{1,3}:\d{4}', ip):
            print("Please, enter node in format: ip:port (ex.: 192.12.0.1:5050)")
            return
        with open("nodes.txt", "a+") as f:
            f.write(ip + "\n")
        print(str(ip) + " was added to list of nodes.")
        
    def submit_tx(self, route, tx):
        requests.post(route, json=tx)

    def prev_hash(self):
        prev_block = block_from_JSON(self.height() - 1)
        prev_hash = prev_block.calculate_hash()
        return prev_hash

    def height(self):
        height = len(self.db)
        return height
    
    def get_difficulty(self):
        diff = self.db.all()[self.height()]['difficulty']
        return diff
    
    def get_current_reward(self):
        denominator = math.pow(2, int(self.height() / 5))
        return int(g_miner_reward / denominator)
       

def to_bitsn(target):
    target_str = str(hex(target))[2:]
    if len(target_str) % 2 == 1:
        target_str = "0" + target_str
    l = len(target_str)
    while target_str[-1] == "0":
        target_str = target_str[:-1]
    res = str(hex(int(l / 2))) + target_str
    return int(res, 16)
    






def test():
    bits = 0x180696f4
    print("Bits: " + str(hex(bits)))
    exp = bits >> 24
    mant = bits & 0xffffff
    target = mant * (1 << (8 * (exp - 3)))
    print("Target: " + str(hex(target)))
    print("to_bits: ", hex(to_bitsn(target)))

if __name__ == "__main__":
    test()


