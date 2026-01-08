from fastapi import FastAPI
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import time
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:apppassword@pgpool:5432/appdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(Integer)
    created_at = Column(Integer, default=lambda: int(time.time()))


@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        count = db.execute(text("SELECT COUNT(*) FROM items")).scalar()
        if count == 0:
            for i in range(100):
                item = Item(
                    name=f"initial_item_{i}",
                    value=random.randint(1, 1000)
                )
                db.add(item)
            db.commit()
            print(f"Added {100} initial items")
        db.close()
    except Exception as e:
        print(f"Startup error: {e}")


@app.post("/write")
def write_item():
    db = SessionLocal()
    
    try:
        is_replica = db.execute(text("SELECT pg_is_in_recovery()")).scalar()

        item = Item(
            name=f"item_{int(time.time())}_{random.randint(1000, 9999)}",
            value=random.randint(1, 1000)
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "id": item.id,
            "name": item.name,
            "value": item.value,
            "written_to": "replica" if is_replica else "master",
            "timestamp": time.time()
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@app.get("/read")
def read_item():
    db = SessionLocal()
    
    try:
        is_replica = db.execute(text("SELECT pg_is_in_recovery()")).scalar()
        result = db.execute(text("SELECT * FROM items ORDER BY RANDOM() LIMIT 1"))
        row = result.fetchone()
        
        if row:
            return {
                "status": "success",
                "id": row[0],
                "name": row[1],
                "value": row[2],
                "read_from": "replica" if is_replica else "master"
            }
        return {"status": "empty", "message": "No items found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
