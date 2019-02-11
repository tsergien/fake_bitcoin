#!/usr/bin/python3

from hashlib import sha256
import wallet
import json
import script

class Transaction():

    def __init__(self, version, inputs, outputs, nLocktime):
        self.version = version
        self.inputs = inputs
        self.outputs = outputs
        self.inp_counter = len(self.inputs)
        self.outp_counter = len(self.outputs)
        self.nLocktime = nLocktime

    def compute_hash(self, serialized):
        s = sha256( sha256( bytes(serialized, "utf-8") ).digest() ).hexdigest()
        return s

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=6)


class CoinbaseTransaction(Transaction):

    def __init__(self, version, inputs, outputs, nLocktime):
        self.version = version
        self.outputs = outputs
        self.inputs = inputs
        self.inp_counter = 1
        self.outp_counter = 1
        self.nLocktime = nLocktime


class Output(object):

    def __init__(self, nVal, recipient):
        self.nVal = nVal
        self.scriptPubKey = script.get_scriptPubKey(recipient)
        self.script_length = int(len(self.scriptPubKey) / 2)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=3)


class Input(object):

    def __init__(self, prev_txid, prev_vout, scriptSig, seq):
        self.txid = prev_txid 
        self.vout = prev_vout
        self.scriptSig = scriptSig
        self.script_length = int(len(scriptSig) / 2) # bytes
        self.seq = 4294967295
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=5)



def output_decoder_helper(obj):
    if '__type__' in obj and obj['__type__'] == 'Output':
        return Output(obj['nVal'], obj['recipient'])
    return obj

def output_json_decoder(obj): 
    out_dict =  json.loads(obj, object_hook=output_decoder_helper)
    recipient = wallet.pubkey_hash_to_address( out_dict['scriptPubKey'][6:-4] )
    return Output(int(out_dict['nVal']), recipient)

def input_decoder_helper(obj):
    if '__type__' in obj and obj['__type__'] == 'Input':
        return Input(obj['txid'], obj['vout'], obj['scriptSig'], obj['seq'])
    return obj

def input_json_decoder(obj): 
    inp_dict =  json.loads(obj, object_hook=output_decoder_helper)
    return Input(inp_dict['txid'], int(inp_dict['vout']), inp_dict['scriptSig'], inp_dict['seq'])

