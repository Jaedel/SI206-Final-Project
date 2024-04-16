import unittest
import sqlite3
import json
import os


# Create Database
def set_up_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    return cur, conn

# TASK 1
# Create table for Patients in SQLite Database
def create_patients_table(cur, conn):
    cur.execute("CREATE TABLE Patients (pet_id INTEGER PRIMARY KEY, name TEXT, species_id INTEGER, age INTEGER, cuteness INTEGER, aggressiveness INTEGER)")
    conn.commit()


# Function to add Sprinkles to the table
def add_sprinkles_info(cur, conn):
    cur.execute("INSERT INTO Patients (name, species, age, cuteness, aggressiveness) VALUES (?, ?, ?, ?, ?)",
                 ("Sprinkles", "Gerbil", 2, 99, 25))
    conn.commit()


# TASK 2
# Function to add DownTheStreet's patient list to your own. For this function assume the table exists
def add_pets_from_json(filename, cur, conn):
    # We've given you this to read in the data from the provided JSON file.
    f = open(filename)
    file_data = f.read()
    f.close()
    json_data = json.loads(file_data)

    # Complete the rest of this function
    id_count = 1
    for i in json_data:
        pet_id = id_count
        name = i("name")
        cur.execute("SELECT id from Species WHERE title = ?", (i["species"],))
        species = int(cur.fetchone()[0])
        age = int(i["age"])
        cuteness = int(i["cuteness"])
        aggressiveness = int(1["aggressiveness"])
        cur.execute(
            "INSERT INTO Patients (pet_id, name, species_id, age, cuteness, aggressiveness) VALUES (?,?,?,?,?,?)"
            (pet_id, name, species, age, cuteness, aggressiveness),
        )
        id_count += 1
    conn.commit()

# TASK 3
# Function to find non aggressive pets for the intern


def non_aggressive_pets(aggressiveness, cur, conn):
    list_of_pet_tuples = []
    cur.execute(f"SELECT name FROM Patients WHERE aggressiveness <= '(aggressiveness)'")
    rows = cur.fetchall()
    for row in rows:
        list_of_pet_tuples.append(row[0])
    return list_of_pet_tuples