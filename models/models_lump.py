import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, TIMESTAMP, func, TypeDecorator, Float
from sqlalchemy.orm import relationship, declarative_base, object_session, sessionmaker

from Env import Env

# Create an in-memory SQLite database
engine = create_engine(f'sqlite:///{Env.DB_FILE}') # , echo=True
Session = sessionmaker(bind=engine)

# Create a base class for declarative models
Base = declarative_base()


class MyTIMESTAMP(TypeDecorator):
    """
    Crutch for SQLAlchemy's inability to handle SQLite TIMESTAMP and DateTime as a string
    """
    impl = TIMESTAMP
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if type(value) is str:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value

class Path(Base):
    __tablename__ = 'paths'

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False, unique=True)

class StudyType(Base):
    __tablename__ = 'study_types'

    id = Column(Integer, primary_key=True)
    type = Column(Text, nullable=False, unique=True)


class ImageMetadata(Base):
    __tablename__ = 'image_metadata'

    image_id = Column(Integer, name='id', primary_key=True)
    filename = Column(Text, nullable=False)
    study_type_id = Column(Integer, ForeignKey('study_types.id'), name='study_type', nullable=False)
    path_id = Column(Integer, ForeignKey('paths.id'), name='path', nullable=False)
    fav = Column(Integer, default=0)
    count = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    lost = Column(Integer, default=0)
    last_viewed = Column(MyTIMESTAMP, default='1999-01-01 00:00:00')
    imported_at = Column(MyTIMESTAMP, default=datetime.now)
    image_hash = Column(Text, name='hash')

    study_type_ref = relationship('StudyType')
    path_ref = relationship('Path')

    @property
    def is_fav(self):
        return self.fav

    @property
    def study_type(self):
        return self.study_type_ref.type

    @property
    def path(self):
        return os.path.join(self.path_ref.path, self.filename)

    @property
    def path_abs(self):
        return os.path.join(Env.IMAGES_PATH, self.path)

    def mark_as_lost(self, session=None, auto_commit=True):
        self.lost = 1
        if session is None:
            session = object_session(self)
            session.commit()
            return

        if auto_commit:
            session.commit()
            return

        session.flush()


    def __str__(self):
        return f"{self.image_id}({self.last_viewed}): {self.path} fav({self.fav}) r({self.rating}) c({self.count}))"

    def __repr__(self):
        return str(self)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(Text, unique=True, nullable=False)
    color_id = Column(Integer, ForeignKey('colors.id'), name='color', nullable=False, default=1)

    @property
    def hex(self):
        return self.color

    def __lt__(self, other):
        return self.tag < other.tag

    def __gt__(self, other):
        return self.tag > other.tag

    def __eq__(self, other):
        return self.tag == other.tag

    def __str__(self):
        return f"({self.id}:{self.tag})"

    def __repr__(self):
        return str(self)

class ImageTag(Base):
    __tablename__ = 'image_tags'

    image_id = Column(Integer, ForeignKey('image_metadata.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

    image = relationship('ImageMetadata', backref='tags') # ?? tag. should it be images?
    tag = relationship('Tag', backref='image_tags')

class TagSet(Base):
    __tablename__ = 'tag_sets'

    id = Column(Integer, primary_key=True)
    set_name = Column(Text, nullable=False, unique=True)
    set_alias = Column(Text, nullable=False, unique=True)
    tag_list = Column(Text)

    def get_tags(self) -> ([int],[int]):
        tags_all = list(map(lambda t: t.strip(), self.tag_list.split(','))) if self.tag_list else []
        tags_pos = [int(t) for t in tags_all if not t.startswith('-')]
        tags_neg = [int(t[1:]) for t in tags_all if t.startswith('-')]
        return tags_pos, tags_neg

    def get_tags_names(self) -> ([str],[str]):
        tags_pos, tags_neg = self.get_tags()
        session = object_session(self)
        tags_pos = [t.tag for t in session.query(Tag).filter(Tag.id.in_(tags_pos))]
        tags_neg = [t.tag for t in session.query(Tag).filter(Tag.id.in_(tags_neg))]

        return tags_pos, tags_neg

class Color(Base):
    __tablename__ = 'colors'

    id = Column(Integer, primary_key=True)
    color_name = Column(Text)
    hex = Column(Text, default='#000000')

    tags = relationship('Tag', backref='color')

    def __str__(self):
        return self.hex

    def __repr__(self):
        return str(self)

class ImageColor(Base):
    __tablename__ = 'image_colors'

    image_id = Column(Integer, ForeignKey('image_metadata.id'), primary_key=True)
    color_id = Column(Integer, ForeignKey('colors.id'), primary_key=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    image = relationship('ImageMetadata', backref='colors')
    color = relationship('Color', backref='images')

    @property
    def position(self):
        return self.x, self.y

class ImageDupe(Base):
    __tablename__ = 'dupes'

    image1 = Column(Integer, name='image1', default=0, primary_key=True)
    image2 = Column(Integer, name='image2', default=0, primary_key=True)
    false_positive = Column(Integer, name='fp', default=0)
    resolved = Column(Integer, name='r', default=0)
    found_at = Column(MyTIMESTAMP, default=datetime.now)

# Create the tables
# Base.metadata.create_all(engine, checkfirst=True)

if __name__ == '__main__':
    print('main!')

    session = Session()

    paths = session.query(Path).all()

    # for p in paths:
    #     print(f'{p.id} {p.path}')

    image_metadata = session.query(ImageMetadata).filter(
        ImageMetadata.rating > 3,
        ImageMetadata.fav == 1
    ).limit(1).all()

    for p in image_metadata:
        print(f'{p.image_id} {p.path.path}/{p.filename} {",".join([t.tag for t in p.tags])}')