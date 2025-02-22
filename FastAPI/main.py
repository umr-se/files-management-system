from fastapi import FastAPI, File, UploadFile, HTTPException, Response, Query
import mysql.connector

app = FastAPI()

# Connect to MySQL Server
connection = mysql.connector.connect(
    host="localhost",  # Replace with your MySQL server host
    user="root",  # Replace with your MySQL username
    password="password",  # Replace with your MySQL password
    database="FileStorageDB"  # Use the correct database
)

cursor = connection.cursor()

# Ensure the database and table are created
cursor.execute("CREATE DATABASE IF NOT EXISTS FileStorageDB")
cursor.execute("USE FileStorageDB")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        data LONGBLOB NOT NULL
    )
""")

# List to store available deleted IDs
deleted_ids = []

@app.delete("/delete")
def delete_file(file_id: int):
    sql = "DELETE FROM Files WHERE id = %s"
    cursor.execute(sql, (file_id,))
    connection.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"No file found with ID {file_id}")

    deleted_ids.append(file_id)

    return {"status": "File deleted successfully", "file_id": file_id}

@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    binary_data = await file.read()

    if deleted_ids:
        reused_id = deleted_ids.pop(0)
        sql = "INSERT INTO Files (id, filename, data) VALUES (%s, %s, %s)"
        cursor.execute(sql, (reused_id, file.filename, binary_data))
        file_id = reused_id
    else:
        sql = "INSERT INTO Files (filename, data) VALUES (%s, %s)"
        cursor.execute(sql, (file.filename, binary_data))
        file_id = cursor.lastrowid

    connection.commit()

    return {"filename": file.filename, "status": "File has been stored in the database", "file_id": file_id}

@app.put("/update")
async def update_file(file_id: int, file: UploadFile = File(...)):
    sql = "SELECT id FROM Files WHERE id = %s"
    cursor.execute(sql, (file_id,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"No file found with ID {file_id}")

    binary_data = await file.read()

    sql = "UPDATE Files SET filename = %s, data = %s WHERE id = %s"
    cursor.execute(sql, (file.filename, binary_data, file_id))
    connection.commit()

    return {"filename": file.filename, "status": "File has been updated successfully", "file_id": file_id}

@app.get("/retrieve")
def retrieve_file(file_id: int = Query(None), filename: str = Query(None)):
    if file_id:
        sql = "SELECT filename, data FROM Files WHERE id = %s"
        cursor.execute(sql, (file_id,))
    elif filename:
        sql = "SELECT filename, data FROM Files WHERE filename = %s"
        cursor.execute(sql, (filename,))
    else:
        raise HTTPException(status_code=400, detail="Either file_id or filename must be provided")

    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="No file found")

    retrieved_filename, binary_data = result

    headers = {
        'Content-Disposition': f'attachment; filename="{retrieved_filename}"'
    }
    return Response(content=binary_data, media_type="application/octet-stream", headers=headers)

@app.on_event("shutdown")
def shutdown_event():
    cursor.close()
    connection.close()
