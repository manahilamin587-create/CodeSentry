def find_user(db, u):
    sql = "SELECT * FROM users "
    sql += "WHERE name='" + u + "'"
    return db.execute(sql)