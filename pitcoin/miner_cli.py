#!/usr/bin/env python3

import cmd
from blockchain import Blockchain, block_from_JSON
import requests
import wallet
import form_tx
from serializer import Serializer
from serializer import Deserializer
import script
import json

class Miner_cli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "\033[1;32;40m > "
        self.intro  = "*** Miner command line interface ***\nType 'help' to get usage.\n"
        self.doc_header = " Commands "
        self.chain = Blockchain()
        try:
            with open("config.conf", "r") as f:
                self.server_port = f.read().replace("\n", "")
        except:
            with open("config.conf", "w") as f:
                f.write("http://127.0.0.1:5000")
            self.server_port = open("config.conf", "r").read().replace("\n", "")

    def do_addnode(self, args):
        print("\033[0;37;40m")
        "Adds node to nodes list of Blockchain (based on received \
        parameter in URL format without scheme)"
        self.chain.add_node(args)

    def do_addr(self, args):
        print("\033[0;37;40m")
        "Shows my current address (just for seeing balance)"
        print("Miner's adress is: " + self.chain.address)

    def do_mine(self, args):
        print("\033[0;37;40m")
        "start mining process. Mine block with getting transactions from pending pool, \
        adding coinbase transaction with miner address from a file, \
        calculation parameters like merkle root, hash and saving block in chain"
        print("Starting mining")
        self.chain.mine()
        print("Stopping mining")

    def do_premine(self, args):
        print("\033[0;37;40m")
        "start auto mining process"
        print("Starting mining")
        addresses =[wallet.gen_address(wallet.wif_to_privkey(self.chain.miner_wif)),\
                    wallet.gen_address(wallet.wif_to_privkey(self.chain.miner_wif)), \
                    wallet.gen_address(wallet.wif_to_privkey(self.chain.miner_wif))]
        if args == "":
            N = 5
        else:
            N = int(args)
        i = 0
        while i < N:
            # sending random transactions between self addresses
            if i != 0:
                self.chain.utxo_pool.update_pool([])
                tx = form_tx.form_transaction(self.chain.address, addresses[i % 3], 70 + i * i, self.chain.utxo_pool, self.chain.miner_wif)
                self.chain.submit_tx(self.server_port + "/transaction/new", Serializer().serialize(tx))
            i += 1
            self.chain.mine()
        print("Stopping mining")

    def do_automine(self, args):
        print("\033[0;37;40m")
        "start auto mining process"
        print("Starting mining")
        nodes = self.chain.get_nodes_list()
        while 1:
            my_len = self.chain.height()
            for node in nodes:
                cur_len = requests.get("http://" + node + "/chain/length")
                if int(cur_len.json()) > my_len:
                    block = requests.get("http://" + node + "/block/receive").json()
                    print("Received: type: " + str(type(block)))
                    print("Received: " + block)
                    self.chain.db.insert(block)
            self.chain.mine()
        print("Stopping mining")

    def do_nodes(self, args):
        print("\033[0;37;40m")
        "Shows my current address (just for seeing balance)"
        try:
            with open("nodes.txt", "r") as f:
                nodes_list = f.read().split("\n")
            for node in nodes_list:
                print("--> " + node)
        except:
            print("There are no nodes.")

    def do_height(self, args):
        print("\033[0;37;40m")
        "Shows how many block there are"
        print(f'Current chain length: {self.chain.height()}')

    def do_last_hash(self, args):
        print("\033[0;37;40m")
        "Shows last block hash"
        print(f'Last block hash: {self.chain.prev_hash()}')

    def do_block_info(self, data):
        print("\033[0;37;40m")
        "Shows lblock info by id"
        if (len(data) < 1):
            print(f'Please enter id of hash of block which info you\'d like to see.')
        print(f'Block[{data}]: {self.chain.get_block_info(data)}')


    def do_consensus(self, args):
        print("\033[0;37;40m")
        "Connect to other nodes and get full chain, compare it and\
        resolve conflicts by choosing more longer chain and replace current"
        self.chain.resolve_conflicts()


    def do_balance(self, args):
        "Shows balance of passed address"
        print("\033[0;37;40m")
        if  not script.check_availability(args):
            print("Please, enter valid address")
            return
        self.chain.utxo_pool.update_pool([])
        print(f'Balance of {args} is: {self.chain.utxo_pool.get_balance(args)}')
    

    def do_history(self, addr):
        print("\033[0;37;40m")
        "Display history of all transactions  made by passed address."
        my_scriptPubKey = script.get_scriptPubKey(addr)
        for i in range(self.chain.height()):
            b = block_from_JSON(i);
            for tx in b.txs:
                tx_d = Deserializer().deserialize(tx)
                for o in tx_d.outputs:
                    if o.scriptPubKey == my_scriptPubKey:
                        print(f'\033[1;32;40mTransaction:\033[0;37;40m {tx_d.toJSON()}')




    def do_exit(self,*args):
        return True

    def default(self, line):
         print("\033[1;31;40m Command is not valid \033[0;37;40m")



if __name__ == "__main__":
    cli = Miner_cli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("Stopping miner_cli")