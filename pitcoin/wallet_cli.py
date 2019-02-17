#!/usr/bin/python3

import wallet
import cmd
import secrets
from transaction import Transaction, Input, Output
from serializer import Serializer, Deserializer
from pending_pool import get_tx
import requests
from blockchain import Blockchain
from base58check import b58decode, b58encode
import script
from hashlib import sha256
from binascii import hexlify, unhexlify
import form_tx
from utxo_set import Utxos


class Cli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "\033[1;32;40m > "
        self.intro  = "\033[1;34;40m*** Wallet command line interface ***\nType 'help' to get usage.\033[0;37;40m\n"
        self.doc_header = "Commands"

        self.server_port = "http://127.0.0.1:5000"
        self.tx_to_broadcast = []
        self.chain = Blockchain()
        self.addresses = []
        try:
            with open("addresses.txt", "r") as f:
                lines = f.readlines()
            for l in lines:
                self.addresses.append(l.replace("\n", ""))
        except:
            pass

        try:
            with open("mnemonic", "r") as f:
                self.mnemonic = f.read().replace("\n", "")
        except:
            with open("mnemonic", "w") as f:
                f.write(wallet.get_mnemonic())
            self.mnemonic = open("mnemonic", "r").read().replace("\n", "")
        self.seed = wallet.get_seed(self.mnemonic) # hex str
        self.master_key, self.chaincode = wallet.get_key_chain(self.seed)

        self.wallet = {
        "seed": self.seed,
        "private_key": self.master_key,
        "wif": wallet.privkey_to_wif(self.master_key),
        "public_key": wallet.get_pubkey_str(self.master_key),
        "xprivate_key": "",
        "xpublic_key": "",
        "address": "",
        "wif": wallet.privkey_to_wif(self.master_key),
        "children": []
        }



    def do_port(self, args):
        print("\033[0;37;40m")
        "Change port"
        if len(args) == 4 and args.isdigit():
            self.server_port = "http://127.0.0.1:" + args
            print("set: " + self.server_port)


    def do_new(self, args):
        "Generates new child private key"
        print("\033[0;37;40m")
        ind = len(self.wallet["children"])
        childm, childc = wallet.get_key_chain(self.wallet["public_key"] + self.chaincode + str(ind))
        self.wallet["children"].append([childm, childc])
        addr = wallet.gen_address(wallet.get_pubkey_str(childm))
        open("addresses.txt", "a+").write(addr)
        print("New child was generated: ")
        print("Child private key: ", childm)
        print("Addres:            ", addr)

    def do_children(self, args):
        "Shows childs private key"
        for c in self.wallet["children"]:
            print(c[0] + "\n")


    def do_send(self, args):
        "Sends amount to recepient: send recipient amount"
        print("\033[0;37;40m")
        try:
            recipient, amount = args.split(" ")
        except:
            print("Please, enter recipient and amount")
            return
        try:
            self.chain.utxo_pool.update_pool([])
            tx = form_tx.form_transaction(self.addresses[0], recipient, int(amount), self.chain.utxo_pool, self.wallet["wif"])
            tx_str = Serializer().serialize(tx)
            self.tx_to_broadcast.append(tx_str)
            print("Serialized: " + tx_str)
        except:
            print("Error. Probably you have not enough money.")


    def do_broadcast(self, args):
        "Sends POST request with serialized transaction data to \
        web API of Pitcoin full node, which provide route /transaction/new\
        (you can use flag -testnet)."
        print("\033[0;37;40m")
        try:
            count = 0
            print("tx to bradcast: " + str(self.tx_to_broadcast))
            for t in self.tx_to_broadcast:
                self.chain.submit_tx(self.server_port + "/transaction/new", t)
                count += 1
            print(str(count) + " txs was broadcasted.")
        except:
            print("No connection")
        self.tx_to_broadcast = []

    def do_get10(self, args):
        print("\033[0;37;40m")
        children_amount = len(self.wallet["children"])
        i = 20
        while children_amount < i:
            childm, childc = wallet.get_key_chain(self.wallet["public_key"] + self.chaincode + str(children_amount))
            self.wallet["children"].append([childm, childc])
            children_amount = len(self.wallet["children"])
            
        k = 0

        print("Receiving: ")
        for k in range(10):
            c = self.wallet["children"][k]
            addr = wallet.gen_address(wallet.get_pubkey_str(c[0]))
            self.addresses.append(addr)
            open("addresses.txt", "a+").write(addr + "\n")
            print(k, ". ", addr)
            k += 1
        print("Change addresses: ")
        for k in range(10, 20):
            c = self.wallet["children"][k]
            addr = wallet.gen_address(wallet.get_pubkey_str(c[0]))
            self.addresses.append(addr)
            open("addresses.txt", "a+").write(addr + "\n")
            print(k - 10, ". ", addr)
            k += 1


    def do_addr(self, args):
        "Shows list of addresses"
        print("\033[0;37;40m")
        print("My addresses:")
        for a in self.addresses:
            print("--> " + a)


    def do_balance(self, args):
        "Shows balance of passed address"
        print("\033[0;37;40m")
        if  not script.check_availability(args):
            print("Please, enter valid address")
            return
        self.chain.utxo_pool.update_pool([])
        print("Balance of " + args + " is: " + str(self.chain.utxo_pool.get_balance(args)))
    

    def do_mybalance(self, args):
        "Shows balance of all my imported addresses"
        print("\033[0;37;40m")
        self.chain.utxo_pool.update_pool([])
        total = 0
        print("Balances of all my addresses: ")
        for a in self.addresses:
            cur_bal = self.chain.utxo_pool.get_balance(a) 
            total += cur_bal
            print("Balance of " + a + " is: " + str(self.chain.utxo_pool.get_balance(a)))
        print("Total balance is: " + str(total))


    def default(self, line):
        print("\033[1;31;40m Command is not valid \033[0;37;40m")

if __name__ == "__main__":
    cli = Cli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("Stopping wallet_cli")