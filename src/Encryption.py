import rsa
from Crypto.PublicKey import RSA

class keyGen:
    def genKeys(self,formID):
        RSA_KEY_PAIR= dict()

        key_pair = RSA.generate(1024)
        private_key = open("RSA_private_key\%s.pem" %formID, "wb")
        private_key.write(key_pair.exportKey("PEM"))
        private_key.close()
        RSA_KEY_PAIR['private_key']=key_pair.exportKey()
        RSA_KEY_PAIR['public_key']=key_pair.publickey().exportKey()
        
        return RSA_KEY_PAIR

class encryption:
    def decrypt(message, privKey):
        crypto = rsa.decrypt(message, privKey)
        message.decode('utf8')
        print(message)