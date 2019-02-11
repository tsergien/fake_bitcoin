#!/usr/bin/python3

OP_DUP = 0x76
OP_HASH160 = 0xa9
OP_EQUALVERIFY = 0x88
OP_CHECKSIG = 0xac

from hashlib import sha256, new
from binascii import unhexlify, hexlify
import ecdsa
import wallet
from base58check import b58decode
import base58


def script_from_hex(s_hex):
    res = ""
    while len(s_hex) != 0:
        b = int(s_hex[:2], 16)
        s_hex = s_hex[2:]
        if b == OP_DUP:
            res += "OP_DUP "
        elif b == OP_HASH160:
            res += "OP_HASH160 "
        elif b == OP_EQUALVERIFY:
            res += "OP_EQUALVERIFY "
        elif b == OP_CHECKSIG:
            res += "OP_CHECKSIG "
        else:
            res += s_hex[:b * 2] + " "
            s_hex = s_hex[b * 2:]
    res = res[:-1]
    return res
 
 #_____________________________________________________________________________________________________
 #_____________________________________________________________________________________________________
 #_____________________________________________________________________________________________________
    # my_private_key = sender_wif_priv
    # my_private_key_hex = base58.b58decode_check(my_private_key)[1:33].hex()
    # pk_bytes = bytes.fromhex(my_private_key_hex)
    # sk = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1)
    # vk = sk.verifying_key
    # can be used for uncompressed pubkey
    # vk_string = vk.to_string()
    # public_key_bytes = b'\04' + vk_string
    # sender_compressed_pub = "02C3C6A89E01B4B62621233C8E0C2C26078A2449ABAA837E18F96A1F65D7B8CC8C"
    # public_key_bytes_hex = sender_compressed_pub
    # signature = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der_canonize)
 #_____________________________________________________________________________________________________
 #_____________________________________________________________________________________________________
 #_____________________________________________________________________________________________________


def get_scriptSig_testnet(wif, message):
    my_private_key_hex = base58.b58decode_check(wif)[1:33].hex()
    pk_bytes = bytes.fromhex(my_private_key_hex)
    sk = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1)
    sig = sk.sign_digest(bytes.fromhex(message), sigencode=ecdsa.util.sigencode_der_canonize)
    sig = hexlify(sig).decode("utf-8")
    pubk = wallet.compressed_pk_from_wif(wif)
    # pubk = wallet.get_pubkey_str(wallet.wif_to_privkey(wif))
    pubk_len = int(len(pubk) / 2)
    sig_len = int(len(sig) / 2) + 1
    res = ( '{:02x}'.format(sig_len) + sig + "01" + '{:02x}'.format(pubk_len) + pubk)
    return res

def get_scriptSig(wif, message):
    sig, pk = wallet.sign_tx(wif, message)
    pubk_len = int(len(pk) / 2)
    sig_len = int(len(sig) / 2) + 1
    res = ( '{:02x}'.format(sig_len) + sig + "01" + '{:02x}'.format(pubk_len) + pk)
    return res

def get_scriptPubKey(address):
    pubkey_hash = hexlify(b58decode(address)).decode("utf-8")[2:-8]
    res = "76a914%s88ac" % pubkey_hash
    return res

def exec_script(scriptSig, scriptPubKey, tx_hash):
    s = scriptSig + scriptPubKey
    stack = []
    while len(s) > 0:
        op = int(s[:2], 16)
        try:
            if op == OP_DUP:
                stack.append( stack[len(stack) -1] )
            elif op == OP_EQUALVERIFY:
                item1 = stack.pop()
                item2 = stack.pop()
                if item1 != item2:
                    print("OP_EQUALVERIFY failed: " + item1 + " != " + item2)
                    return False
            elif op == OP_HASH160:
                item = stack.pop()
                res = sha256(unhexlify(item)).hexdigest()
                h = new('ripemd160')
                h.update(unhexlify(res))
                res = h.hexdigest()
                stack.append(res)
            elif op == OP_CHECKSIG:
                pk = stack.pop()
                sig = stack.pop()[:-2]
                vk = ecdsa.VerifyingKey.from_string(unhexlify(pk[2:]), curve=ecdsa.SECP256k1)
                # if not vk.verify_digest( bytes.fromhex(sig), tx_hash.encode('utf-8'), sigdecode=ecdsa.util.sigdecode_der):
                if not vk.verify( bytes.fromhex(sig), tx_hash.encode('utf-8')):
                    print("Veryfing signature failed")
                    return False
            else:
                op *= 2
                stack.append( s[2:op + 2] )
                s = s[op:]
            s = s[2:]
        except:
            print("Script: except")
            return False
    if len(stack) == 0:
        print("script OK. stack is empty")
        return True
    return False



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


def test():
    " SCRIPT  TEST "
    privkey = wallet.gen_privkey()
    wif = wallet.privkey_to_wif( privkey )
    pubkey = wallet.get_pubkey_str(privkey)
    address = wallet.gen_address(pubkey)

    scriptSig = get_scriptSig(wif, "1234567890abcdef1234567890")
    print("scriptSig: " + scriptSig)
    scriptPubKey = get_scriptPubKey( address )
    print("scriptPubKey: " + scriptPubKey)
    
    if exec_script(scriptSig, scriptPubKey, "1234567890abcdef1234567890"):
        print("script is correct")
    # if not exec_script(scriptSig, scriptPubKey, "1234567890abcdee."):
    #     print("script is  NOT correct")

if __name__ == "__main__":
    test()

