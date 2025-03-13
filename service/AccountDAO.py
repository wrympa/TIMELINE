import sqlite3


class AccountDAO:
    def __init__(self):
        self.conn = sqlite3.connect("DBs/identifier.sqlite")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                name TEXT PRIMARY KEY,
                pass TEXT NOT NULL,
                points INTEGER DEFAULT 0
            )
        ''')

        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        if self.cursor.fetchone()[0] == 0:
            initial_accounts = [
                ("A", "1", 0),
                ("B", "1", 0),
                ("C", "1", 0),
                ("D", "1", 0)
            ]
            self.cursor.executemany(
                "INSERT INTO accounts (name, pass, points) VALUES (?, ?, ?)",
                initial_accounts
            )

        self.conn.commit()

    def addAccount(self, username, password) -> bool:
        try:
            self.cursor.execute("SELECT name FROM accounts WHERE name = ?", (username,))
            if self.cursor.fetchone():
                return False  # Username already exists

            self.cursor.execute(
                "INSERT INTO accounts (name, pass, points) VALUES (?, ?, 0)",
                (username, password)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def attemptAuth(self, username, password) -> bool:
        try:
            self.cursor.execute(
                "SELECT pass FROM accounts WHERE name = ?",
                (username,)
            )
            result = self.cursor.fetchone()

            if not result:
                return False  # Username doesn't exist

            return result[0] == password
        except sqlite3.Error:
            return False

    def addPoints(self, username, points) -> bool:
        try:
            self.cursor.execute("SELECT name FROM accounts WHERE name = ?", (username,))
            if not self.cursor.fetchone():
                return False  # Username doesn't exist

            self.cursor.execute(
                "UPDATE accounts SET points = points + ? WHERE name = ?",
                (points, username)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()