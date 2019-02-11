#!/usr/bin/python3

from hashlib import sha256, new
from binascii import unhexlify, hexlify
from base58check import b58encode, b58decode
import ecdsa

def privkey_to_wif(ext_privkey):
    ext_privkey = "80" + ext_privkey
    privkey_b = unhexlify(ext_privkey)
    checksum = str( sha256(sha256(privkey_b).digest()).hexdigest() )[:8]
    ext_privkey = ext_privkey + checksum
    WIF = b58encode(unhexlify(ext_privkey)).decode("utf-8")
    return WIF

def wif_to_privkey(wif_str):
    decoded_wif = b58decode(wif_str)
    privkey = hexlify(decoded_wif)
    privkey = privkey[2:-8]
    return privkey.decode("utf-8")

def gen_privkey():
    return ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1).to_string().hex()

def get_pubkey_str(privkey_str):
    privkey = unhexlify(privkey_str)
    sk = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    pubkey = "04" + vk.to_string().hex()
    return pubkey

def gen_address(pubkey_str):
    pubkey_hash = sha256(unhexlify(pubkey_str)).hexdigest()
    h = new('ripemd160')
    h.update(unhexlify(pubkey_hash))
    pubkey_hash = "00" + h.hexdigest()
    pubkey_b = unhexlify(pubkey_hash)
    checksum = str(sha256(sha256(pubkey_b).digest()).hexdigest())[:8]
    pubkey_hash = pubkey_hash + checksum
    address = b58encode(unhexlify(pubkey_hash)).decode("utf-8")
    return address

def sign_tx(wif, message):
    privkey = wif_to_privkey(wif)
    pubkey = get_pubkey_str(privkey)
    sk = ecdsa.SigningKey.from_string(unhexlify(privkey), curve=ecdsa.SECP256k1)
    signature = sk.sign(message.encode()).hex()
    return (signature, pubkey)
 
def pubkey_hash_to_address(pubkey_hash):
    pubkey_hash = "00" + pubkey_hash
    pubkey_b = unhexlify(pubkey_hash)
    checksum = str(sha256(sha256(pubkey_b).digest()).hexdigest())[:8]
    return b58encode( unhexlify(pubkey_hash + checksum)).decode("utf-8")

def compressed_pk_from_wif(wif):
    privkey = wif_to_privkey(wif)
    pk = get_pubkey_str(privkey)
    pref = "03"
    if int(pk[66:], 16) % 2 == 0:
        pref = "02"
    return (pref + pk[2:66])












#############################################################################
def testing_stuff():
    privkey = gen_privkey()
    pubkey = get_pubkey_str(privkey)
    wif = privkey_to_wif(privkey)
    message = "hell"

    signature = sign_tx(wif, message)
    vk = ecdsa.VerifyingKey.from_string(unhexlify(pubkey[2:]), curve=ecdsa.SECP256k1)
    if  vk.verify(unhexlify(signature[0]), message.encode('utf-8')):
        print("ok")
    else:
        print("not ok")

    pubkey_hash = sha256(unhexlify(pubkey)).hexdigest()
    h = new('ripemd160')
    h.update(unhexlify(pubkey_hash))
    print(pubkey_hash_to_address(pubkey_hash))
    
if __name__ == "__main__":
    testing_stuff()