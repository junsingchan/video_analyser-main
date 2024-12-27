# 使用示例:
"""
# 创建具体模型
from .models import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    name = Column(String(50))
    email = Column(String(100))

# 使用示例
connection_string = "mysql+pymysql://user:password@localhost/dbname"
db = Database(connection_string)
db.create_tables()

# 插入单条记录
user = User(name="John", email="john@example.com")
db.insert_one(user)

# 批量插入
users = [
    User(name="Alice", email="alice@example.com"),
    User(name="Bob", email="bob@example.com")
]
db.insert_many(users)

# 查询
user = db.get_by_id(User, 1)
all_users = db.get_all(User)

# 更新
user.name = "John Smith"
db.update(user)

# 删除
db.delete(user)
"""
