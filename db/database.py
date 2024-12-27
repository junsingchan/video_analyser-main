from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


class Database:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """创建所有表"""
        from .base import Base
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self):
        """提供session上下文管理器"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def insert_one(self, model_instance):
        """插入单条记录"""
        with self.session_scope() as session:
            session.add(model_instance)

    def insert_many(self, model_instances):
        """批量插入记录"""
        with self.session_scope() as session:
            session.add_all(model_instances)

    def get_by_id(self, model_class, id):
        """根据ID查询"""
        with self.session_scope() as session:
            return session.query(model_class).get(id)

    def get_all(self, model_class):
        """获取所有记录"""
        with self.session_scope() as session:
            return session.query(model_class).all()

    def update(self, model_instance):
        """更新记录"""
        with self.session_scope() as session:
            session.merge(model_instance)

    def delete(self, model_instance):
        """删除记录"""
        with self.session_scope() as session:
            session.delete(model_instance)