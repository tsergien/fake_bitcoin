#!/usr/bin/python3

import cmd
from blockchain import Blockchain
import requests

# do_conbsensus

class Miner_cli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "\033[1;32;40m > "
        self.intro  = "*** Miner command line interface ***\nType 'help' to get usage.\n"
        self.doc_header = " Commands "
        self.chain = Blockchain()

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

    def do_chainlen(self, args):
        print("\033[0;37;40m")
        "Shows my current address (just for seeing balance)"
        print("Current chain length: " + str(self.chain.height()))

    def do_consensus(self, args):
        print("\033[0;37;40m")
        "Connect to other nodes and get full chain, compare it and\
        resolve conflicts by choosing more longer chain and replace current"
        self.chain.resolve_conflicts()

    def default(self, line):
         print("\033[1;31;40m Command is not valid \033[0;37;40m")

if __name__ == "__main__":
    cli = Miner_cli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("Stopping miner_cli")