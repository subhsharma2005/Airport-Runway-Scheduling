from typing import List
import heapq
import tkinter as tk
from tkinter import messagebox, ttk
from database import FlightDatabase
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def time_to_minutes(time_str: str) -> int:
    try:
        hours, minutes = map(int, time_str.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
        return hours * 60 + minutes
    except ValueError:
        raise ValueError("Time must be in HH:MM format (00:00 to 23:59)")

def minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

class Flight:
    def __init__(self, id: int, scheduled_time: str, duration: int):
        self.id = id
        self.scheduled_time_str = scheduled_time
        self.scheduled_time = time_to_minutes(scheduled_time)
        self.duration = duration
        self.start_time = 0
        self.runway = -1

    def __lt__(self, other):
        return self.scheduled_time < other.scheduled_time

def schedule_flights(flights: List[Flight], runway_count: int) -> List[Flight]:
    flights.sort()
    runway_heap = []
    for i in range(runway_count):
        heapq.heappush(runway_heap, (0, i))
    
    scheduled_flights = []
    
    for flight in flights:
        earliest_available, runway_number = heapq.heappop(runway_heap)
        flight.start_time = max(earliest_available, flight.scheduled_time)
        flight.runway = runway_number
        heapq.heappush(runway_heap, (flight.start_time + flight.duration, runway_number))
        scheduled_flights.append(flight)
    
    return scheduled_flights

class FlightHistoryWindow:
    def __init__(self, parent, db):
        self.window = tk.Toplevel(parent)
        self.window.title("Flight History")
        self.window.geometry("1200x600")
        self.db = db
        
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.table_frame = ttk.Frame(self.main_frame)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("ID", "Scheduled Time", "Start Time", "Delay", "Runway"), show="headings", height=10)
        self.tree.heading("ID", text="Flight ID")
        self.tree.heading("Scheduled Time", text="Scheduled Time")
        self.tree.heading("Start Time", text="Start Time")
        self.tree.heading("Delay", text="Delay (min)")
        self.tree.heading("Runway", text="Runway")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        self.load_data()
    
    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        flights = self.db.get_all_flights()
        
        if not flights:
            return
        
        flight_data = []
        
        for flight in flights:
            self.tree.insert("", "end", values=(
                flight[1],
                minutes_to_time(flight[2]),
                minutes_to_time(flight[4]),
                flight[6],
                flight[5] + 1
            ))
            flight_data.append({
                'id': flight[1],
                'scheduled_time': flight[2],
                'start_time': flight[4],
                'delay': flight[6],
                'runway': flight[5]
            })
        
        flight_data.sort(key=lambda x: x['scheduled_time'])
        
        flight_ids = [f['id'] for f in flight_data]
        delays = [f['delay'] for f in flight_data]
        scheduled_times = [minutes_to_time(f['scheduled_time']) for f in flight_data]
        
        self.ax.clear()
        
        bars = self.ax.bar(range(len(flight_ids)), delays, color='skyblue', alpha=0.7)
        
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}min',
                        ha='center', va='bottom')
        
        self.ax.set_xlabel('Flights (ordered by scheduled time)')
        self.ax.set_ylabel('Delay (minutes)')
        self.ax.set_title('Flight Delays Over Time')
        
        self.ax.set_xticks(range(len(flight_ids)))
        self.ax.set_xticklabels(scheduled_times, rotation=45)
        
        self.ax.grid(True, linestyle='--', alpha=0.3)
        
        avg_delay = sum(delays) / len(delays) if delays else 0
        self.ax.axhline(y=avg_delay, color='red', linestyle='--', alpha=0.5,
                       label=f'Average Delay: {avg_delay:.1f} min')
        
        self.ax.legend()
        
        self.fig.tight_layout()
        
        self.canvas.draw()

class AirportSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Airport Runway Scheduler")
        self.db = FlightDatabase()
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.flight_id_label = ttk.Label(self.main_frame, text="Flight ID:")
        self.flight_id_label.grid(row=0, column=0, padx=5, pady=5)
        self.flight_id_entry = ttk.Entry(self.main_frame)
        self.flight_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.scheduled_time_label = ttk.Label(self.main_frame, text="Scheduled Time (HH:MM):")
        self.scheduled_time_label.grid(row=1, column=0, padx=5, pady=5)
        self.scheduled_time_entry = ttk.Entry(self.main_frame)
        self.scheduled_time_entry.grid(row=1, column=1, padx=5, pady=5)
        self.scheduled_time_entry.insert(0, "00:00")
        
        self.duration_label = ttk.Label(self.main_frame, text="Duration (minutes):")
        self.duration_label.grid(row=2, column=0, padx=5, pady=5)
        self.duration_entry = ttk.Entry(self.main_frame)
        self.duration_entry.grid(row=2, column=1, padx=5, pady=5)
        
        self.add_flight_button = ttk.Button(self.main_frame, text="Add Flight", command=self.add_flight)
        self.add_flight_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        self.runway_count_label = ttk.Label(self.main_frame, text="Number of Runways:")
        self.runway_count_label.grid(row=4, column=0, padx=5, pady=5)
        self.runway_count_entry = ttk.Entry(self.main_frame)
        self.runway_count_entry.grid(row=4, column=1, padx=5, pady=5)
        
        self.schedule_button = ttk.Button(self.main_frame, text="Schedule Flights", command=self.schedule_flights)
        self.schedule_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        self.view_history_button = ttk.Button(self.main_frame, text="View Flight History", command=self.show_flight_history)
        self.view_history_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
        
        self.clear_history_button = ttk.Button(self.main_frame, text="Clear Flight History", command=self.clear_flight_history)
        self.clear_history_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        
        self.tree = ttk.Treeview(self.main_frame, columns=("ID", "Scheduled Time", "Start Time", "Delay", "Runway"), show="headings")
        self.tree.heading("ID", text="Flight ID")
        self.tree.heading("Scheduled Time", text="Scheduled Time")
        self.tree.heading("Start Time", text="Start Time")
        self.tree.heading("Delay", text="Delay (min)")
        self.tree.heading("Runway", text="Runway")
        self.tree.grid(row=8, column=0, columnspan=2, padx=5, pady=5)
        
        self.flights = []
    
    def add_flight(self):
        try:
            flight_id = int(self.flight_id_entry.get())
            scheduled_time = self.scheduled_time_entry.get()
            duration = int(self.duration_entry.get())
            
            time_to_minutes(scheduled_time)
            
            self.flights.append(Flight(flight_id, scheduled_time, duration))
            
            self.flight_id_entry.delete(0, tk.END)
            self.scheduled_time_entry.delete(0, tk.END)
            self.scheduled_time_entry.insert(0, "00:00")
            self.duration_entry.delete(0, tk.END)
            
            messagebox.showinfo("Success", "Flight added successfully!")
        except ValueError as e:
            messagebox.showerror("Error", str(e) if str(e) else "Invalid input! Please enter valid numbers and time in HH:MM format.")
    
    def schedule_flights(self):
        try:
            runway_count = int(self.runway_count_entry.get())
            
            if not self.flights:
                messagebox.showerror("Error", "No flights added!")
                return
            
            scheduled_flights = schedule_flights(self.flights, runway_count)
            
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            for flight in scheduled_flights:
                delay = max(0, flight.start_time - flight.scheduled_time)
                self.tree.insert("", "end", values=(
                    flight.id,
                    flight.scheduled_time_str,
                    minutes_to_time(flight.start_time),
                    delay,
                    flight.runway + 1
                ))
                
                self.db.add_flight(
                    flight.id,
                    flight.scheduled_time,
                    flight.duration,
                    flight.start_time,
                    flight.runway,
                    delay
                )
            
            self.flights = []
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number of runways! Please enter a valid number.")
    
    def show_flight_history(self):
        FlightHistoryWindow(self.root, self.db)
    
    def clear_flight_history(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all flight history?"):
            self.db.clear_all_flights()
            for row in self.tree.get_children():
                self.tree.delete(row)
            messagebox.showinfo("Success", "Flight history cleared successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = AirportSchedulerApp(root)
    root.mainloop()