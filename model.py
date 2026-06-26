from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import sqlite3

app = FastAPI()


def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()



class UserCreate(BaseModel):
    name: str
    age: int = Field(gt=0, lt=150)


class UserUpdate(BaseModel):
    name: str
    age: int = Field(gt=0, lt=150)


class UserResponse(BaseModel):
    id: int
    name: str
    age: int


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        (user.name, user.age)
    )

    conn.commit()
    user_id = cursor.lastrowid

    cursor.execute(
        "SELECT id, name, age FROM users WHERE id = ?",
        (user_id,)
    )

    created_user = dict(cursor.fetchone())

    conn.close()
    return created_user



@app.get("/users", response_model=List[UserResponse])
def get_users():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, age FROM users")
    users = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return users


def get_user(user_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, age FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(user)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET name = ?, age = ?
        WHERE id = ?
        """,
        (user.name, user.age, user_id)
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute(
        "SELECT id, name, age FROM users WHERE id = ?",
        (user_id,)
    )

    updated_user = dict(cursor.fetchone())

    conn.close()
    return updated_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.close()

    return {"message": "User deleted successfully"}