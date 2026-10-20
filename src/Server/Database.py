from rocksdict import Rdict

db = Rdict("ledger_db")

class DataBase:

    @staticmethod
    def deleteDatabase():
        for keys in list(db.keys()):
            del db[keys]

        db.flush()

    @staticmethod
    def fetchAllData():
        return db.items()

    @staticmethod
    def saveTestData(data:dict):
        add, commit, TransKey, amt, i = data["add"], data["commit"], data["TransKey"], data["amt"], data["i"]
        db[f"add:{add}"] = {'commit': commit, 'TransKey': TransKey, 'index': 0, 'amt': amt, 'i': i}
