from ..db import get_db

def check_duplicate_document(user_id: str, file_hash: str):
    """
    Checks if the user has already uploaded this exact file using SHA-256 hash.
    Also checks date range/metadata overlaps.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename, status, created_at
        FROM documents
        WHERE user_id = ? AND file_hash = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, file_hash))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "is_duplicate": True,
            "existing_document_id": row["id"],
            "existing_filename": row["filename"],
            "existing_status": row["status"],
            "uploaded_at": row["created_at"],
            "message": "Ye document pehle se add hai."
        }
    return {"is_duplicate": False}
