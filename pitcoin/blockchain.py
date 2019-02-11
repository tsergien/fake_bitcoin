#!/usr/bin/python3

from transaction import Transaction, CoinbaseTransaction, Output
from block import Block, block_from_JSON
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
import time
from form_tx import form_coinbase, form_transaction

g_miner_reward = 5000
halving_time = 1
first_prev_txid = "00000000000000000000000000000000000000000000000000000000000000"

class Blockchain():

    def __init__(self):
        self.db = TinyDB('blks.json')
        self.utxo_pool = Utxos()
        try:
            self.complexity = int( open("complexity", "r").read() )
            self.miner_reward = int( open("miner_reward", "r").read() )
        except:
            self.complexity = 0
            self.miner_reward = g_miner_reward
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
        t0 = time.time()
        coinbase_tx = form_coinbase(self.address, self.miner_wif, self.miner_reward)
        txs = pending_pool.get_first3()
        serialized_cb = Serializer().serialize(coinbase_tx)
        txs.insert(0, serialized_cb)
        nonce = 1
        b = Block(time.time(), self.prev_hash(), txs, nonce).mine(self.complexity)
        self.db.insert({'t': b.timestamp, 'nonce': b.nonce, 'prev_hash': b.prev_hash, 'txs': b.txs, 'hash': b.hash, 'merkle': b.merkle})
        print("Height: " + str(self.height()))
        self.utxo_pool.update_pool(txs)
        print("time: " + str(time.time() - t0))
        if time.time() - t0 < halving_time:
            self.update_complexity(self.complexity + 1)
        if self.height() % 5 == 0 and self.height() > 0:
            self.update_reward(int(self.miner_reward / 2))

    def genesis_block(self):
        t0 = time.time()
        serialized_cb = Serializer().serialize( form_coinbase(self.address, self.miner_wif, self.miner_reward) )
        txs = [serialized_cb]
        nonce = 1
        b = Block(time.time(), first_prev_txid, txs, nonce).mine(self.complexity)
        self.db.insert({'t': b.timestamp, 'nonce': b.nonce, 'prev_hash': b.prev_hash, 'txs': b.txs, 'hash': b.hash, 'merkle': b.merkle})
        print("Height: " + str(self.height()))
        self.utxo_pool.update_pool(txs)
        if time.time() - t0 < halving_time:
            self.update_complexity(self.complexity + 1)
        if self.height() % 5 == 0 and self.height() > 0:
            self.update_reward(int(self.miner_reward / 2))


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
            for c in chain:
                print("BLOCK----> " + str(c))
                self.db.insert(c)
            self.update_complexity( int(requests.get("http://" + node + "/getDifficulty").json()) )
            self.update_reward( int(requests.get("http://" + node + "/getReward").json()) )
        self.utxo_pool.update_pool([])


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
                nodes.append(l)
            f.close()
            return nodes
        except:
            return []

    def add_node(self, ip):
        if not re.match(r'(\d{1,3}\.){3}\d{1,3}:\d{4}', ip):
            print("Please, enter node in format: ip:port (ex.: 192.12.0.1:5050)")
            return
        with open("nodes.txt", "a+") as f:
            f.write(ip)
        print(str(ip) + " was added to list of nodes.")
        
    def submit_tx(self, route, tx):
        requests.post(route, json=tx)

    def prev_hash(self):
        prev_hash = self.db.all()[-1]['hash']
        return prev_hash

    def height(self):
        height = len(self.db)
        return height
    
    def difficulty(self):
        return self.complexity

    def update_complexity(self, new_complexity):
        if new_complexity != self.complexity:
            print("Complexity set to: " + str(new_complexity))
        self.complexity = new_complexity
        open("complexity", "w").write(str(self.complexity))
    
    def update_reward(self, new_reward):
        if new_reward != self.miner_reward:
            print("Miner reward set to: " + str(new_reward))
        self.miner_reward = new_reward
        open("miner_reward", "w").write(str(self.miner_reward))



    