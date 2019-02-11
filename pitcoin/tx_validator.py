#!/usr/bin/python3

from transaction import Transaction
from transaction import CoinbaseTransaction
import wallet
import ecdsa
from binascii import unhexlify
from binascii import hexlify
import codecs
from base58check import b58decode
from hashlib import sha256
import script

def check_availability(address):
    if not 26 <= len(address) <= 35 \
        or not (address[0] == '1' or address[0] == '3'):
        print("Sender's/recipient's address isn't valid")
        return 0
    try:
        decoded = hexlify(b58decode(address))
    except:
        print("Addresses encoding isn't valid: " + address)
        return 0
    c1 = sha256( sha256(unhexlify( decoded[:-8].decode("utf-8") )).digest() ).hexdigest()
    checksum = str( c1 )[:8]
    if checksum != decoded.decode("utf-8")[-8:]:
        print("Addresses checksum isn't valid: " + checksum + " != " + decoded.decode("utf-8")[-8:])
        return 0
    return 1

