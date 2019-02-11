#!/usr/bin/python3

import wallet
from transaction import Transaction, Output, Input, CoinbaseTransaction
import array
import struct
from binascii import hexlify, unhexlify
import codecs

def little_endian(s):
	a = codecs.decode(s, 'hex')[::-1]
	res = codecs.encode( a, 'hex'  ).decode()
	return res

def script_len_to_hex(l):
	if l <= 0xfc:
		return '{:02x}'.format(l)
	elif l <= 0xffff:
		return "fd" + little_endian('{:04x}'.format(l))
	elif l <= 0xffffff:
		return "fe" + little_endian('{:08x}'.format(l))
	else:
		return "ff" + little_endian('{:016x}'.format(l))

def get_script_length(s):
	if s[:2] == "ff":
		return int(little_endian(s[2:18]), 16) * 2, 18
	elif s[:2] == "fe":
		return int(little_endian(s[2:10]), 16) * 2, 10
	elif s[:2] == "fd":
		return int(little_endian(s[2:6]), 16) * 2, 6
	else:
		return int(s[:2], 16) * 2, 2

# B - 2, L - 4, Q - 8
class Serializer():

	def serialize(self, tx):
		s = struct.pack("<L", tx.version)
		s += struct.pack("<B", tx.inp_counter)
		for i in range(0, tx.inp_counter):
			s += bytes.fromhex( little_endian(tx.inputs[i].txid) )
			s += struct.pack("I", tx.inputs[i].vout)
			s += bytes.fromhex( script_len_to_hex(tx.inputs[i].script_length) )
			s += bytes.fromhex(tx.inputs[i].scriptSig)
			s +=  struct.pack("<L", tx.inputs[i].seq)
		s += struct.pack("<B", tx.outp_counter)
		for i in range(0, tx.outp_counter):
			s += struct.pack("<Q", tx.outputs[i].nVal)
			s += bytes.fromhex( script_len_to_hex(tx.outputs[i].script_length) )
			s += bytes.fromhex(tx.outputs[i].scriptPubKey)
		s += struct.pack("<L", tx.nLocktime)
		s = hexlify(s).decode('utf-8')
		# print("SERIALIZED: " + str(s))
		return s

class Deserializer():

	def deserialize(self, serial):
		# try:
		inputs = []
		outputs = []
		version = int(little_endian(serial[:8]), 16)
		serial = serial[8:]
		inp_count = int(serial[:2], 16)
		serial = serial[2:]
		for i in range(0, inp_count):
			shift, input = self.deserialize_input(serial)
			serial = serial[shift:]
			inputs.append(input)
		outp_count = int(serial[:2], 16)
		serial = serial[2:]
		for i in range(0, outp_count):
			shift, output = self.deserialize_output(serial)
			serial = serial[shift:]
			outputs.append(output)
		nLocktime = int(little_endian(serial), 16)
		tx = Transaction(version, inputs, outputs, nLocktime)
		# print("\nDESERIALIZED: " + tx.toJSON())
		return tx
		# except:
			# print("Cant deserialize not valid P2PKH transaction")

	def deserialize_input(self, serial): 
		txid = little_endian(serial[:64])
		serial = serial[64:]
		vout = int(little_endian(serial[:8]), 16)
		serial = serial[8:]
		slen, shift1 = get_script_length(serial)
		serial = serial[shift1:]
		scriptSig = serial[:slen]
		serial = serial[slen:]
		seq = int( little_endian(serial[:8]), 16)
		serial = serial[8:]
		shift = 80 + slen + shift1
		return (shift, Input(txid, vout, scriptSig, seq))

	def deserialize_output(self, serial):
		nVal = int(little_endian( serial[:16] ), 16)
		serial = serial[16:]
		slen, shift1 = get_script_length(serial)
		serial = serial[shift1:]
		scriptPubKey = serial[:slen]
		serial = serial[slen:]
		shift = 16 + slen + shift1
		return (shift, Output(nVal, wallet.pubkey_hash_to_address(scriptPubKey[6:-4])))







import script
import form_tx
import utxo_set
def test_serializer():
	# prev_txid = "169164473ef95f5bdc7860ff5bae37b0cf50ce19ecf99aa0e0fc4377c7d3f713"
	# privkey = wallet.gen_privkey()
	# pubkey = wallet.get_pubkey_str(privkey)
	# recipient = wallet.gen_address(pubkey)
	# wif = wallet.privkey_to_wif(privkey)
	
	# scriptSig = script.get_scriptSig(wif, prev_txid)
	# print("scriptSig_______: " + scriptSig)
	# scriptPubKey = script.get_scriptPubKey(recipient)
	# print("scriptPubKey_______: " + str(scriptPubKey))

	# output1 = Output(256, recipient)
	# input1 = Input(prev_txid, 0, scriptSig, 1)
	# outputs = [output1]
	# inputs = [input1]
	# tx = Transaction(1, inputs, outputs, 0)

	# print("TRANSACTION AT START: " + tx.toJSON())
	# serial = Serializer().serialize(tx)

	# deserial = Deserializer().deserialize(serial)
	# serial2 = Serializer().serialize(deserial)
	# if serial == serial2:
	# 	print("serializer + deserializer: OK")
	# else:
	# 	print("Not ok")
	# if script.exec_script(deserial.inputs[0].scriptSig, deserial.outputs[0].scriptPubKey, deserial.inputs[0].txid):
	# 	print("script OK")

	sender = "1EsE1f1QHn21WVtjGGFNQ8U24R6B5ufqCE"
	wif = "5JgEG4MZKTuoNTqHJiu8DQHHrGU7z45ufHHiVNfkxfjbjbuMpza"
	recipient = "1MAapNpNj5ch9uxToiKgCMeQeoVTaMoZDV"
	utxo_obj = utxo_set.Utxos()
	tx = form_tx.form_transaction(sender, recipient, 178, utxo_obj, wif)
	print("\nBEFORE: tx: " + tx.toJSON())
	serial = Serializer().serialize(tx)
	des = Deserializer().deserialize(serial)



if __name__ == "__main__":
	test_serializer()

