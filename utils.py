import base64
import hashlib

from cryptography.fernet import Fernet

import drive_api


def encrypt(file_data):
    key = Fernet.generate_key()

    f = Fernet(key)
    key_standard_b64 = base64.standard_b64encode(base64.urlsafe_b64decode(key)).decode('utf-8')
    token = f.encrypt(file_data)
    encrypted_data = base64.urlsafe_b64decode(token)
    return {'data': encrypted_data, 'key': key_standard_b64}


def decrypt(encrypted_data, key):
    f = Fernet(base64.urlsafe_b64encode(base64.standard_b64decode(key.encode('utf-8'))))
    token = base64.urlsafe_b64encode(encrypted_data)
    return f.decrypt(token)


def verify_data(file_data, hash):
    m = hashlib.md5()
    m.update(file_data)
    if hash != base64.b64encode(m.digest()).decode("utf-8"):
        raise RuntimeError('Different hash!')


def retrieve_file(service, filename, key):
    encrypted_file_data = drive_api.download_file(service, filename)
    file_data = decrypt(encrypted_file_data, key)
    verify_data(file_data, hash)
    return file_data
