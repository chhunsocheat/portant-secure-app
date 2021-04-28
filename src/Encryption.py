import rsa

class keyGen:
    def genKeys():
        keypair = (pubkey, privkey) = rsa.newkeys(512)
        return keypair

class encryption:
    def decrypt(message, privKey):
        crypto = rsa.decrypt(message, privKey)
        message.decode('utf8')
        print(message)