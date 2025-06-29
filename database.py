import sqlite3
from datetime import datetime

class FlightDatabase:
    def __init__(self, db_name="flights.db"):
        self.db_name = db_name
        self.create_tables()
    
    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY,
            flight_id INTEGER,
            scheduled_time INTEGER,
            duration INTEGER,
            start_time INTEGER,
            runway INTEGER,
            delay INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_flight(self, flight_id, scheduled_time, duration, start_time, runway, delay):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO flights (flight_id, scheduled_time, duration, start_time, runway, delay)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (flight_id, scheduled_time, duration, start_time, runway, delay))
        
        conn.commit()
        conn.close()
    
    def get_all_flights(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM flights ORDER BY created_at DESC')
        flights = cursor.fetchall()
        
        conn.close()
        return flights
    
    def clear_all_flights(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM flights')
        
        conn.commit()
        conn.close() 