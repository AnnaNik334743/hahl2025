from fastapi import FastAPI
import psycopg2
import random
import time
import os
from contextlib import contextmanager

app = FastAPI()

MASTER_URL = os.getenv("MASTER_URL", "postgresql://appuser:apppassword@postgres-master/appdb")
REPLICA_URL = os.getenv("REPLICA_URL", "postgresql://appuser:apppassword@postgres-replica/appdb")


def get_master_conn():
    return psycopg2.connect(MASTER_URL)


def get_replica_conn():
    return psycopg2.connect(REPLICA_URL)


@contextmanager
def get_connection(use_master=True):
    conn = None
    try:
        if use_master:
            conn = get_master_conn()
        else:
            conn = get_replica_conn()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


@app.get("/read")
def read(percent: int = 20, id: int = None):
    use_replica = random.randint(1, 100) <= percent
    
    try:
        if use_replica:
            with get_connection(use_master=False) as conn:
                cur = conn.cursor()
                if id:
                    cur.execute("SELECT id, name FROM items WHERE id = %s", (id,))
                else:
                    cur.execute("SELECT id, name FROM items ORDER BY RANDOM() LIMIT 1")
                
                result = cur.fetchone()
                cur.close()
                
                if result:
                    return {
                        "id": result[0],
                        "name": result[1],
                        "read_from": "replica",
                        "percent": percent
                    }
                return {"error": "No item found", "read_from": "replica"}
        
        else:
            with get_connection(use_master=True) as conn:
                cur = conn.cursor()
                if id:
                    cur.execute("SELECT id, name FROM items WHERE id = %s", (id,))
                else:
                    cur.execute("SELECT id, name FROM items ORDER BY RANDOM() LIMIT 1")
                
                result = cur.fetchone()
                cur.close()
                
                if result:
                    return {
                        "id": result[0],
                        "name": result[1],
                        "read_from": "master",
                        "percent": percent
                    }
                else:
                    return {"error": "No item found", "read_from": "master"}
        
    except Exception as e:
        return {
            "error": str(e), 
            "read_from": "replica" if use_replica else "master",
            "percent": percent
        }


@app.post("/write")
def write(data: str = None):
    try:
        with get_connection(use_master=True) as conn:
            cur = conn.cursor()
            
            item_name = data if data else f"item_{int(time.time())}_{random.randint(1000, 9999)}"
            
            cur.execute(
                "INSERT INTO items (name) VALUES (%s) RETURNING id",
                (item_name,)
            )
            item_id = cur.fetchone()[0]
            
            cur.close()
            
            return {
                "id": item_id,
                "name": item_name,
                "written_to": "master"
            }
        
    except Exception as e:
        return {"error": str(e)}
