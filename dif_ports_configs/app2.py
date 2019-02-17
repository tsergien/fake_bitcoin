#!/usr/bin/python3

from transaction import Transaction
from serializer import Deserializer, Serializer
from flask import Flask, request, jsonify
import pending_pool
import json
from blockchain import Blockchain
from tinydb import TinyDB


app = Flask(__name__)

@app.route('/transaction/new', methods=['POST'])
def tx_new():
	serialized_tx = request.data.decode()[1:-1]
	deserial = Deserializer().deserialize(serialized_tx)
	if Serializer().serialize(deserial) != serialized_tx:
		print("Cant append invalid transactoiin to pending pool")
	pending_pool.get_tx(serialized_tx)
	print("Serialized transaction: " + str(serialized_tx) + " was added to the pending pool.")
	return ""

@app.route('/transaction/pending', methods=['GET'])
def tx_pending():
	pending = []
	try:
		with open("mempool.dat", "r") as f:
			lines = f.read().splitlines()
		for st in lines:
			pending.append(Deserializer().deserialize(st).toJSON())
	except:
		return "There are no transactions in mempool"
	return jsonify(pending)

@app.route('/chain', methods=['GET'])
def chain():
	db = TinyDB('blks.json')
	return jsonify(db.all())

@app.route('/nodes', methods=['GET'])
def nodes():
	return jsonify(Blockchain().get_nodes_list())

@app.route('/chain/length', methods=['GET'])
def chain_length():
	return jsonify(Blockchain().height())

@app.route('/getDifficulty', methods=['GET'])
def get_difficulty():
	try:
		diff = int(open("complexity", "r").read())
	except:
		return "0"
	return str(diff)

@app.route('/getReward', methods=['GET'])
def get_reward():
	try:
		reward = int(open("miner_reward", "r").read())
	except:
		return "5000"
	return str(reward)


@app.route('/block/receive', methods=['GET'])
def get_receiveblock():
	block = Blockchain().db.all()[-1]
	print("Block t receive: " + str(type((block))))
	# print("Block t receive: " + jsonify(block))
	return str(block)


if __name__ == "__main__":
	app.run(debug=True,  port=5002)
