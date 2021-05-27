from sqlalchemy import Column, Integer, Boolean, String, MetaData, Table
from sqlalchemy_enum34 import EnumType

from monitorrent.db import Base, UTCDateTime
from monitorrent.upgrade_manager import add_upgrade
from monitorrent.plugins.status import Status


class TopicPolymorphicMap(dict):
    base_mapper = None

    def __getitem__(self, key):
        if key not in self:
            return self.base_mapper
        return super(TopicPolymorphicMap, self).__getitem__(key)

    def __setitem__(self, key, value):
        if not self.base_mapper:
            self.base_mapper = value
        super(TopicPolymorphicMap, self).__setitem__(key, value)


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    last_update = Column(UTCDateTime, nullable=True)
    type = Column(String)
    status = Column(EnumType(Status, by_name=True), nullable=False, server_default=Status.Ok.__str__())
    paused = Column(Boolean(create_constraint=False), nullable=False, server_default='0')
    download_dir = Column(String, nullable=True)
    download_category = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'topic',
        'polymorphic_on': type,
        'with_polymorphic': '*',
        '_polymorphic_map': TopicPolymorphicMap()
    }


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), Topic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        with operations_factory() as operations:
            quality_column = Column('status', String(8), nullable=False, server_default=Status.Ok.__str__())
            operations.add_column(Topic.__tablename__, quality_column)
        version = 1
    if version == 1:
        with operations_factory() as operations:
            paused_column = Column('paused', Boolean(create_constraint=False), nullable=False, server_default='0')
            operations.add_column(Topic.__tablename__, paused_column)
        version = 2
    if version == 2:
        with operations_factory() as operations:
            download_dir_column = Column('download_dir', String, nullable=True, server_default=None)
            operations.add_column(Topic.__tablename__, download_dir_column)
        version = 3
    if version == 3:
        with operations_factory() as operations:
            download_category_column = Column('download_category', String, nullable=True, server_default=None)
            operations.add_column(Topic.__tablename__, download_category_column)
        version = 4


def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(Topic.__tablename__, m, autoload=True)
    if 'status' not in topics.columns:
        return 0
    if 'paused' not in topics.columns:
        return 1
    if 'download_dir' not in topics.columns:
        return 2
    if 'download_category' not in topics.columns:
        return 3
    return 4


add_upgrade(upgrade)
