#!/usr/bin/env python3

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
        "children": []
        }
        self.wif_address = {}


    def do_port(self, args):
        print("\033[0;37;40m")
        "Change port"
        if len(args) == 4 and args.isdigit():
            self.server_port = "http://127.0.0.1:" + args
            print("set: " + self.server_port)


    def do_new_key(self, args):
        "Generates new pair of public and private keys"
        privkey = wallet.gen_privkey()
        wif = wallet.privkey_to_wif(privkey)
        vk = wallet.get_pubkey_str(privkey)
        pub_address = wallet.gen_address(vk)
        self.wallet["wif"] = wif
        self.addresses.append(pub_address)
        f = open("addresses.txt", "a+")
        f.write(pub_address + "\n")
        f.close()
        print("Private key : " + privkey)
        print("Address     : " + pub_address)


    def do_new_child(self, args):
        "Generates new child private key"
        print("\033[0;37;40m")
        ind = len(self.wallet["children"])
        childm, childc = wallet.get_key_chain(self.wallet["public_key"] + self.chaincode + str(ind))
        self.wallet["children"].append([childm, childc])
        addr = wallet.gen_address(wallet.get_pubkey_str(childm))
        self.addresses.append(addr)
        open("addresses.txt", "a+").write(addr+ "\n")
        print("New child was generated: ")
        print("Child private key: ", childm)
        print("Addres:            ", addr)

    def do_import(self, path):
        "Import WIF from file: import PATH"
        if not path:
            print("Please, enter path to file.")
            return
        try:
            self.wallet["wif"] = open(path, "r").read(51)
            privkey = wallet.wif_to_privkey(self.wallet["wif"])
            pubkey = wallet.get_pubkey_str(privkey)
            self.addresses.append(wallet.gen_address(pubkey))
            f = open("addresses.txt", "a+")
            f.write(self.addresses[-1] + "\n")
            f.close()
            print("Private key ( WIF ): " + self.wallet["wif"] + " was imported to wallet")
            print("Public address     : " + self.addresses[-1])
        except:
            print("File " + path + " doesn't exist or has invalid form ( WIF needed )")

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
        # try:
        if args:
            self.chain.utxo_pool.update_pool([])
            print("pool updated.")
            tx = form_tx.form_transaction(self.addresses[-1], recipient, int(amount), self.chain.utxo_pool, self.wallet["wif"])
            print("tx.formed")
            tx_str = Serializer().serialize(tx)
            self.tx_to_broadcast.append(tx_str)
            print("Serialized: " + tx_str)
        # except:
            # print("Error. Probably you have not enough money.")


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
        init_chil = children_amount
        for i in range(20):
            childm, childc = wallet.get_key_chain(self.wallet["public_key"] + self.chaincode + str(children_amount + i))
            self.wallet["children"].append([childm, childc])
            children_amount = len(self.wallet["children"])
            
        print("Receiving: ")
        for k in range(10):
            c = self.wallet["children"][init_chil + k]
            addr = wallet.gen_address(wallet.get_pubkey_str(c[0]))
            self.addresses.append(addr)
            open("addresses.txt", "a+").write(addr + "\n")
            print(k, ". ", addr)
        print("Change addresses: ")
        for k in range(10, 20):
            c = self.wallet["children"][init_chil + k]
            addr = wallet.gen_address(wallet.get_pubkey_str(c[0]))
            self.addresses.append(addr)
            open("addresses.txt", "a+").write(addr + "\n")
            print(k - 10, ". ", addr)


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
        unique_addr = set(self.addresses)
        print("Balances of all my addresses: ")
        for a in unique_addr:
            cur_bal = self.chain.utxo_pool.get_balance(a) 
            total += cur_bal
            print("Balance of " + a + " is: " + str(self.chain.utxo_pool.get_balance(a)))
        print("Total balance is: " + str(total))

    def do_exit(self,*args):
        return True

    def default(self, line):
        print("\033[1;31;40m Command is not valid \033[0;37;40m")

if __name__ == "__main__":
    cli = Cli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("Stopping wallet_cli")