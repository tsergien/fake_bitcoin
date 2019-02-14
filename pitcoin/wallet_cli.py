#!/usr/bin/python3

import wallet
import cmd
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

        self.tx_to_broadcast = []
        self.chain = Blockchain()
        self.server_ip = "http://127.0.0.1:5000"
        self.wif_address = {}
        self.wif = ""
        self.address = ""
        self.testnet = 0
        self.utxo = Utxos()

    def do_port(self, args):
        print("\033[0;37;40m")
        "Change port"
        if len(args) == 4 and args.isdigit():
            self.server_ip = "http://127.0.0.1:" + args
            print("set: " + self.server_ip)

    def do_new(self, args):
        "Generates new pair of public and private keys"
        print("\033[0;37;40m")
        privkey = wallet.gen_privkey()
        wif = wallet.privkey_to_wif(privkey)
        vk = wallet.get_pubkey_str(privkey)
        pub_address = wallet.gen_address(vk)
        self.wif_address[wif] = pub_address
        self.wif = wif
        self.address = pub_address
        f = open("addresses.txt", "a+")
        f.write(pub_address + "\n")
        f.close()
        print("Private key : " + privkey)
        print("Address     : " + pub_address)

    def do_import(self, path):
        "Import WIF from file: import PATH"
        print("\033[0;37;40m")
        if not path:
            print("Please, enter path to file.")
            return
        try:
            self.wif = open(path, "r").read(51)
            privkey = wallet.wif_to_privkey(self.wif)
            pubkey = wallet.get_pubkey_str(privkey)
            pub_address = wallet.gen_address(pubkey)
            self.address = pub_address
            self.wif_address[self.wif] = pub_address
            f = open("addresses.txt", "a+")
            f.write(pub_address + "\n")
            f.close()
            print("Private key ( WIF ): " + self.wif + " was imported to wallet")
            print("Public address     : " + pub_address)
        except:
            print("File " + path + " doesn't exist or has invalid forma ( WIF needed )")


    def do_send(self, args):
        "Sends amount to recepient: send recipient amount"
        print("\033[0;37;40m")
        try:
            recipient, amount = args.split(" ")
        except:
            print("Please, enter recipient and amount")
            return
        if self.wif == "":
            print("Please, type new to generate key or import file to import from file")
            return
        try:
            self.chain.utxo_pool.update_pool([])
            tx = form_tx.form_transaction(self.address, recipient, int(amount), self.utxo, self.wif)
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
            if args == "-testnet":
                self.testnet = 1
            count = 0
            print("tx to bradcast: " + str(self.tx_to_broadcast))
            for t in self.tx_to_broadcast:
                self.chain.submit_tx(self.server_ip + "/transaction/new", t)
                count += 1
            print(str(count) + " txs was broadcasted( testenet = " + str(self.testnet) + " )")
        except:
            print("No connection")
        self.tx_to_broadcast = []


    def do_seemempool(self, args):
        "Shows transactions from the mempool in JSON"
        print("\033[0;37;40m")
        try:
            requests.post(self.server_ip + "/transaction/pending")
        except:
            print("No connection")
            return


    def do_addr(self, args):
        "Shows list of addresses"
        print("\033[0;37;40m")
        print("My addresses:")
        for a in self.wif_address.values():
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
        for a in self.wif_address.values():
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