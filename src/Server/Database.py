from rocksdict import Rdict

db = Rdict("ledger_db")

class DataBase:
    @staticmethod
    def enter_data(publicKey, nonce):
        db[f"acc:{publicKey}"] = {'nonce': nonce}

    @staticmethod
    def update(publicKey):
        acct = db[f"acc:{publicKey}"]
        acct['nonce'] += 1
        db[f"acc:{publicKey}"] = acct

    @staticmethod
    def fetch_data(publicKey):
        acct = db[f"acc:{publicKey}"]
        return acct['nonce']

    @staticmethod
    def fetchAllData():
        return db.items()

    @staticmethod
    def saveTestData(data:dict):
        oneTimeAdd, commit, TransKey = data["oneTimeAddress"], data["commit"], data["TransKey"]
        db[f"add:{oneTimeAdd}"] = {'commit': commit, 'TransKey': TransKey, 'index': 0}
