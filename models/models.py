from sqlalchemy import JSON, Column, Integer, String, Text
from sqlalchemy.sql.sqltypes import Integer
from db.database import Base
    
class SqlParsers(Base):
    __tablename__ = "sqlparsers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    input_query = Column(Text)
    modified_query = Column(Text)
    hashed_column_map = Column(JSON)