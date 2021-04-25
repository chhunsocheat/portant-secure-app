import rsa

class keyGen:
    def genKeys():
        keypair = (pubkey, privkey) = rsa.newkeys(512)
        return keypair

class encryption:
    def decrypt(message, keypair):
        # message = ""
        # keypair = KeyGen.genKeys()
        crypto = rsa.decrypt(message, keypair[1])
        message.decode('utf8')
        print(message)