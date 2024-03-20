import pymongo


class Repository:
    def __init__(self):
        self.connection = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.connection["shop"]


class ProductRepository(Repository):
    def __init__(self):
        super().__init__()
        self.collection = self.db["products"]

    def get_all(self):
        return list(self.collection.find({"visible": True}))

    def get_by_id(self, _id):
        return self.collection.find_one({"id": _id})

    def get_by_user(self, user):
        return list(self.collection.find({"buyer": user}).sort("buy_time", 1))

    def add(self, product):
        return self.collection.insert_one(product)

    def delete(self, _id):
        return self.collection.update_one({"id": _id}, {"$set": {"visible": False}})

    def update(self, _id, product):
        return self.collection.update_one({"id": _id}, {"$set": product})


class UserRepository(Repository):
    def __init__(self):
        super().__init__()
        self.collection = self.db["users"]

    def get_all(self):
        return list(self.collection.find({"visible": True}))

    def get_by_id(self, _id):
        return self.collection.find_one()

    def add(self, user):
        return self.collection.insert_one(user)

    def update(self, _id, user):
        return self.collection.update_one({"id": _id}, {"$set": user})

    def delete(self, _id):
        return self.collection.update_one({"id": _id}, {"$set": {"visible": False}})


user_repo = UserRepository()
product_repo = ProductRepository()
