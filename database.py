from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    is_approved = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    last_active = Column(DateTime, default=None, nullable=True)

engine = create_engine("sqlite:///data/db.sqlite", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Add default admin if not exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", is_approved=True, is_admin=True)
        db.add(admin)
        db.commit()
    db.close()
