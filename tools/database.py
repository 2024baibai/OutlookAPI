import sqlite3 
from threading import Lock

db_lock = Lock()


class Database:

    def __init__(self):
        self.db_file = './database.db'
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def get_cursor(self):
        if not hasattr(self, 'cursor'):
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
        return self.cursor
    

    def create_table(self):
        with self.get_cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS outlook_emails (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email VARCHAR(255) UNIQUE,
                                email_password VARCHAR(255),
                                client_id VARCHAR(255),
                                refresh_token TEXT,
                                access_token TEXT,
                                expire_time TIMESTAMP,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                              )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS email_records (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email VARCHAR(255),
                                subject TEXT,
                                content TEXT,
                                sender VARCHAR(255),
                                received_time TIMESTAMP,
                                UNIQUE(email, subject, sender, received_time)
                                )''')
            
            self.conn.commit()
        
    def execute(self, query, params=()):
        cursor = self.get_cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def get_expired_tokens(self):
        cursor = self.execute("SELECT * FROM outlook_emails WHERE expire_time <= datetime('now')")
        return cursor.fetchall()
    
    def update_token(self, email, new_refresh_token,new_access_token,new_expire_time):
        self.execute('''UPDATE outlook_emails 
                        SET refresh_token = ?, access_token = ?, expire_time = ? 
                        WHERE email = ?''', 
                     (new_refresh_token, new_access_token, new_expire_time, email))

    def add_email(self, email, email_password, client_id, refresh_token, access_token, expire_time):
        self.execute('''INSERT OR IGNORE INTO outlook_emails 
                        (email, email_password, client_id, refresh_token, access_token, expire_time) 
                        VALUES (?, ?, ?, ?, ?, ?)''', 
                     (email, email_password, client_id, refresh_token, access_token, expire_time))

    def batch_add_emails(self, email_list):
        with db_lock:
            with self.get_cursor() as cursor:
                cursor.executemany('''INSERT OR IGNORE INTO outlook_emails 
                                      (email, email_password, client_id, refresh_token, access_token, expire_time) 
                                      VALUES (?, ?, ?, ?, ?, ?)''', 
                                   email_list)
                self.conn.commit()        



        