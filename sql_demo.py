import csv
import time
import mysql.connector

conn = mysql.connector.connect(host="localhost", user="root", password="toquanghan25")
cur = conn.cursor()

# 1. Tạo DB và 2 bảng (DDL)
cur.execute("CREATE DATABASE IF NOT EXISTS imdb_demo CHARACTER SET utf8mb4")
cur.execute("USE imdb_demo")
cur.execute("DROP TABLE IF EXISTS ratings")
cur.execute("DROP TABLE IF EXISTS titles")
cur.execute("CREATE TABLE titles (tconst VARCHAR(20) PRIMARY KEY, title TEXT, year INT)")
cur.execute("CREATE TABLE ratings (tconst VARCHAR(20) PRIMARY KEY, rating FLOAT, votes INT)")
conn.commit()

# 2. CÁCH 1: Insert từng dòng bằng execute() - chạy thử 1000 dòng để đo tốc độ
t0 = time.time()
with open("title.ratings.tsv", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    next(reader)  # Bỏ qua dòng tiêu đề
    for i, row in enumerate(reader):
        if i == 10000:
            break
        cur.execute("INSERT INTO ratings VALUES (%s, %s, %s)", (row[0], float(row[1]), int(row[2])))
        conn.commit()
print(f"Cách 1 (execute 1000 dòng): {time.time() - t0:.2f} giây")

# 3. CÁCH 2: Insert theo lô bằng executemany() - nạp toàn bộ 2 file (>1.5 triệu & >11.5 triệu dòng)
cur.execute("TRUNCATE TABLE ratings")
conn.commit()

def load_batch(filename, sql, parse_fn, batch_size=50000):
    t_start = time.time()
    batch, total = [], 0
    with open(filename, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            batch.append(parse_fn(row))
            if len(batch) == batch_size:
                cur.executemany(sql, batch)
                conn.commit()
                total += len(batch)
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
            conn.commit()
            total += len(batch)
    print(f"Cách 2 ({filename} - {total:,} dòng): {time.time() - t_start:.2f} giây")

load_batch("title.ratings.tsv", "INSERT INTO ratings VALUES (%s, %s, %s)",
           lambda r: (r[0], float(r[1]), int(r[2])))

load_batch("title.basics.tsv", "INSERT INTO titles VALUES (%s, %s, %s)",
           lambda r: (r[0], r[2], None if r[5] == r"\N" else int(r[5])))

# 4. Truy vấn JOIN kiểm tra dữ liệu 2 bảng
cur.execute("""
    SELECT t.title, t.year, r.rating, r.votes
    FROM titles t JOIN ratings r ON t.tconst = r.tconst
    WHERE r.votes > 1000000 ORDER BY r.rating DESC LIMIT 5
""")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()