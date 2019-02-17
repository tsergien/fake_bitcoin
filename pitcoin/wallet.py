#!/usr/bin/python3

from hashlib import sha256, new, pbkdf2_hmac, sha512
import hmac
from binascii import unhexlify, hexlify
from base58check import b58encode, b58decode
import ecdsa
import secrets
from bitstring import BitArray

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


def get_mnemonic():
    with open("words.txt", "r") as f:
        lines = f.readlines()
    result = []
    result_str = ""
    entropy = str(hex(secrets.randbits(128)))[2:]
    if len(entropy) % 2 == 1:
        entropy = "0" + entropy
    bin_entropy = BitArray(hex=entropy).bin
    print("Entropy: ", entropy)
    checksum = sha256( sha256(unhexlify(entropy)).digest() ).hexdigest()
    checksum = BitArray(hex=checksum).bin
    # print("CHecksum: ", str(checksum)[:4])
    entropy = str(bin_entropy) + str(checksum)[:4]
    # print("Entropy + checksum: ", entropy) #1094210d270840daec7b5cc0000f0bef398f - 36-> 18 bytes -> 106 bits
    for i in range(12):
        ind = int(entropy[ (11*i) : (11*(i + 1)) ], 2)
        result_str += lines[ind].replace("\n", " ")
        result.append(lines[ind].replace("\n", "") )##################################
    print("\033[1;31;40m Mnemonic: ", result_str, "\033[0;37;40m")
    return result_str[:-1]


def get_seed(mnemonic_str):
    password = "salt"
    s = pbkdf2_hmac('sha512', bytes(mnemonic_str.encode('utf-8')), bytes(password.encode('utf-8')), 2048)
    s = str(hexlify(s))[2:-1]
    print("Seed: ", s)
    return s

def get_key_chain(seed_hex_str):
    res = hmac.new(bytes(seed_hex_str.encode('utf-8')), digestmod=sha512).digest()
    res = str(hexlify(res))[2:-1]
    m = res[:64]
    c = res[64:]
    return m, c







#############################################################################
def testing_stuff():
    privkey = gen_privkey()
    pubkey = get_pubkey_str(privkey)
    wif = privkey_to_wif(privkey)
    message = "hell"
#################
    m = get_mnemonic()
    seed = get_seed(m)
    m, c = get_key_chain(seed)
    M = get_pubkey_str(m)
    print("Master private key: ", m)
    print("Chaincode:          ", c)
    print("Public M:           ", M)



if __name__ == "__main__":
    testing_stuff()