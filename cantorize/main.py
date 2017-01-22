#!/usr/bin/env python

from Crypto.Cipher import AES
from Crypto.Protocol import KDF
from getpass import getpass
import argparse
import subprocess
import binascii

# Blocksize by default is 16 bytes for AES-128.
BLOCKSIZE = 16

NUM_REPO = dict(
    dict({i: str(i) for i in range(10)}).items() +
    dict({10: 'a', 11: 'b', 12: 'c', 13: 'd',
          14: 'e', 15: 'f', 16: 'g'}).items()
)

# Crypto.get_random_bytes()
SALT = '_\x94\xdb\xbd\xd8\xdd?5\xff\xb5\xe1\x9d\xbe\n\x16\xc2'
IV = '\x03\x0c\x06\xf0B\xdb\xcbv!0\xe4\xea"\xc3;-'


def argument_handler():
    parser = argparse.ArgumentParser()
    arg_group = parser.add_mutually_exclusive_group(required=True)
    arg_group.add_argument("-e", "--encrypt", help="Encrypt a text",
                           action='store_true')
    arg_group.add_argument("-d", "--decrypt", help="Decrypt a text",
                           action='store_true')
    arg_group.add_argument("-i", "--interactive", action='store_true')
    parser.add_argument("-m1", "--first_message",
                        help="What's your first message?",
                        type=str)
    parser.add_argument("-m2", "--second_message",
                        help="What's your second message?",
                        type=str)
    parser.add_argument("-p1", "--first_password",
                        help="What's the password for the first message?",
                        type=str)
    parser.add_argument("-p2", "--second_password",
                        help="What's the password for the second message?",
                        type=str)
    parser.add_argument("-m0", "--ciphertext", type=str)
    parser.add_argument("-p0", "--paired_password", type=str)
    args = parser.parse_args()
    return (args.encrypt, args.decrypt, args.first_message,
            args.second_message, args.first_password, args.second_password,
            args.ciphertext, args.paired_password, args.interactive)


def get_password():
    password = None
    confirmation = False
    while confirmation != password:
        password = getpass("What is your encryption password? ")
        confirmation = getpass("Repeat your password: ")
        if password != confirmation:
            print "Your password doesn't match its confirmation"
    return password



def base_10_to_b(decimal, b):
    new_num_string = ''
    current = decimal
    while current != 0:
        current, remainder = divmod(current, b)
        if 26 > remainder > 9:
            remainder_string = NUM_REPO[remainder]
        else:
            remainder_string = str(remainder)
        new_num_string = remainder_string + new_num_string
    return new_num_string


def base_b_to_10(number, b):
    result = 0
    number = list(str(number))
    number.reverse()
    for i in range(len(number)):
        for j in NUM_REPO:
            if number[i] == NUM_REPO[j]:
                result += int(j) * b ** int(i)
    return result


def gen_key(password, salt, dkLen=BLOCKSIZE):
    return KDF.PBKDF2(str(password), salt, dkLen=BLOCKSIZE)


def pad(plaintext):
    topad = BLOCKSIZE - (len(plaintext) % BLOCKSIZE)
    padded = str(plaintext + bytearray([topad] * topad))
    return padded


def unpad(padded_plaintext):
    bytestring = bytearray(padded_plaintext)
    padding_char = bytestring[-1]
    plaintext = str(bytestring[: len(bytestring) - padding_char])
    return plaintext


def encrypt(text, password, salt=SALT, IV=IV):
    padded_text = pad(text)
    key = gen_key(password, salt)
    cipher = AES.AESCipher(key, AES.MODE_CBC, IV=IV)
    ciphertext_b256 = cipher.encrypt(padded_text)
    ciphertext_b16 = binascii.hexlify(bytearray(ciphertext_b256))
    ciphertext_b10 = base_b_to_10(ciphertext_b16, 16)
    return ciphertext_b10


def decrypt(ciphertext, password, salt=SALT, IV=IV):
    ciphertext_b16 = base_10_to_b(ciphertext, 16)
    ciphertext_original = binascii.unhexlify(ciphertext_b16)
    key = gen_key(password, salt)
    cipher = AES.AESCipher(key, AES.MODE_CBC, IV=IV)
    padded_plaintext = cipher.decrypt(ciphertext_original)
    return unpad(padded_plaintext)


def pair_ciphertexts(c1, c2):
    return subprocess.check_output("wolframscript ./Pair {} {}".format(c1, c2),
                                   shell=True).rstrip().split('\n')[0]


def depair_ciphertexts(c):
    column = subprocess.check_output(
        "wolframscript ./Depair {}".format(c),
        shell=True).rstrip().split('\n')[0]
    wlist = column[len("Column"):].split(',')
    return map(long, (wlist[0][1:], wlist[1][1: len(wlist[1]) - 1]))


if __name__ == '__main__':
    (should_encrypt, should_decrypt, first_message, second_message,
     first_password, second_password, ciphertext,
     paired_password, interactive) = argument_handler()
    if should_encrypt:
        ciphertext_1 = encrypt(first_message, first_password)
        ciphertext_2 = encrypt(second_message, second_password)
        paired = pair_ciphertexts(ciphertext_1, ciphertext_2)
        print(paired)
    elif should_decrypt:
        ciphertext_1, ciphertext_2 = depair_ciphertexts(ciphertext)
        try:
            m1 = decrypt(ciphertext_1, paired_password)
        except:
            m1 = ""
        try:
            m2 = decrypt(ciphertext_2, paired_password)
        except:
            m2 = ""
        print(m1, m2)
    elif interactive:
        paired = None
        choice = None
        while choice not in set(["e", "d", "q"]):
            choice = str(raw_input("(e)ncrypt or (d)ecrypt or (q)uit? "))
            if choice == "e":
                message_1 = str(raw_input("Enter first message: "))
                pass_1 = get_password()
                message_2 = str(raw_input("Enter second message: "))
                pass_2 = get_password()
                print("Processing...")
                c1 = encrypt(message_1, pass_1)
                c2 = encrypt(message_2, pass_2)
                paired = pair_ciphertexts(c1, c2)
                print "The first ciphertext: \n{}".format(c1)
                print "The second ciphertext: \n{}".format(c2)
                print "The paired ciphertext: \n{}".format(paired)
                choice = None
            elif choice == "d":
                if paired is None:
                    paired = str(raw_input("What's the paired ciphertext? "))
                password = get_password()
                print "processing"
                c1, c2 = depair_ciphertexts(paired)
                print "The result is: \n{}".format(decrypt(c1, password),
                                                   decrypt(c2, password))
                choice = None
            elif choice == "q":
                raise SystemExit

