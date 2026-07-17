import bcrypt


def hash_password(plain_password:str)->str:
    '''
        Erzeugt bcypt hash

    '''
    if plain_password is None:
        raise ValueError("Password not none")
    if plain_password =="":
        raise ValueError("Password must be an non-empty string!")
    
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password:str, stored_hash:str)->bool:
    if not plain_password or not stored_hash:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"),stored_hash.encode("utf-8"))
