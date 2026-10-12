import psycopg

# Connect to the default database to create the test database
conn = psycopg.connect("host=localhost port=5432 user=lenny_user password=local_dev_password dbname=postgres", autocommit=True)
try:
    conn.execute("CREATE DATABASE lenny_assistant_test")
    print("Test database created.")
except psycopg.errors.DuplicateDatabase:
    print("Test database already exists.")
conn.close()

# Connect to the new database to create the pgvector extension
conn = psycopg.connect("host=localhost port=5432 user=lenny_user password=local_dev_password dbname=lenny_assistant_test", autocommit=True)
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
print("Extension 'vector' ensured in test database.")
conn.close()
