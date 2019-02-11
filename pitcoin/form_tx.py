#!/usr/bin/python3

from serializer import Serializer, Deserializer
from transaction import Output, Input, Transaction, CoinbaseTransaction
from hashlib import sha256
import script
from utxo_set import Utxos
from binascii import unhexlify

coinbase_txid = "0000000000000000000000000000000000000000000000000000000000000000"
tx_fee = 10
satoshi = 10000000



# class Input(self, prev_txid, prev_vout, scriptSig, seq):
def form_coinbase(miner_address, wif, g_miner_reward):
    outputs = [ Output(g_miner_reward, miner_address) ]
    inputs = []
    scriptSig = script.get_scriptSig(wif, "tanya works better") # it can contain any data i like :)
    inputs.append( Input(coinbase_txid, 0xffffffff, scriptSig, 0xffffffff) )
    return CoinbaseTransaction(1, inputs, outputs, 0)

def get_signed_scriptSig(spendable_output, inputs_outpoint_dict, outputs, wif):
    scriptSig = spendable_output.output.scriptPubKey
    inputs_outpoint_dict[spendable_output].scriptSig = scriptSig # set only this input scriptPubKey
    inputs = []
    for v in inputs_outpoint_dict.values():
        inputs.append(v)
    tx = Transaction(1, inputs, outputs, 0)
    serial = Serializer().serialize(tx)
    message = sha256( sha256(unhexlify(serial)).digest() ).hexdigest()
    scriptSig = script.get_scriptSig(wif, message)
    return scriptSig

def form_transaction(sender, recipient, amount, utxo_obj, wif):
    outputs = []
    inputs = []
    spendable_utxo = utxo_obj.get_outputs_to_spend(sender, int(amount) + tx_fee)
    if len(spendable_utxo) == 0:
        raise Exception("Address " + sender + " has not enough spendable outputs, can't form transaction")
    utxo_sum = 0
    for v in spendable_utxo:
       utxo_sum += v.output.nVal
    outputs.append( Output(int(amount), recipient) )
    if utxo_sum - int(amount) - tx_fee > 0:
        outputs.append( Output(utxo_sum - int(amount) - tx_fee, sender ))

    inputs_outpoint_dict = {} #  {spendable_output : input}
    for outs in spendable_utxo:
        inputs_outpoint_dict[outs] = Input(outs.txid, int(outs.vout, 16), "", 0xffffffff)

    # forming scriptSig for all inputs
    scripts = {} # {spendable_output : scriptSig}
    for spendable_output in inputs_outpoint_dict.keys():
        scripts[spendable_output] =  get_signed_scriptSig(spendable_output, inputs_outpoint_dict.copy(), outputs, wif)

    for k in scripts.keys():
        inputs.append( Input(k.txid, int(k.vout, 16), scripts[k], 0xffffffff) )
    return Transaction(1, inputs, outputs, 0)






import wallet
def testing_forming():
    privkey = wallet.gen_privkey()
    wif = wallet.privkey_to_wif(privkey)

    sender = wallet.gen_address( wallet.get_pubkey_str(privkey) )
    recipient = wallet.gen_address( wallet.get_pubkey_str(wallet.gen_privkey()) )
    utxo_obj = Utxos()
    g_miner_reward = 50

    coinbase_tx = form_coinbase(recipient, wif, g_miner_reward)
    print(coinbase_tx.toJSON())
    serial_coinbase = Serializer().serialize(coinbase_tx)
    deserial_coinbase = Deserializer().deserialize(serial_coinbase)


    # tx = form_transaction(sender, recipient, 0.005, utxo_obj, wif)
    # print(tx.toJSON())

if __name__ == "__main__":
    testing_forming()



