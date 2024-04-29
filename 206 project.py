import requests
import sqlite3
import json
import os

NYT_API_KEY = 'Y4YC23d1jbw0W2Y9pu5NgxFWFm1Mrz8p'

def new_api_key():
    new_dict = {}
    publisher_dict = {}
    num_value = 0
    publisher = 0
    published_date = '2022-04-01'
    response = requests.get(url=f'https://api.nytimes.com/svc/books/v3/lists/full-overview.json?published_date={published_date}&api-key={NYT_API_KEY}')
    if response.status_code == 200:
        data = json.loads(response.text)
        for item in data["results"]["lists"]:
            for i in item["books"]:
                if i["publisher"] not in publisher_dict.keys():
                    num_value += 1
                    publisher_dict[i["publisher"]] = num_value
                publisher = publisher_dict[i["publisher"]]
                new_dict[i["primary_isbn13"]] = [i["title"], i["rank"], publisher]
    return new_dict

def get_rating(isbn):
    '''
    creates API request
    ARGUMENTS: 
        title: ISBN of the book you're searching for 

    RETURNS: 
        float with the rating OR None if the 
        request was unsuccesful
    '''

    isbn_url = f'https://openlibrary.org/isbn/{isbn}.json'
    isbn_response = requests.get(isbn_url)
    if isbn_response.status_code == 200:
        isbn_dict = isbn_response.json()
        works_key = isbn_dict["works"][0]["key"]
        works_id_list = works_key.split("/")
        works_id = works_id_list[-1]

        works_url = f'https://openlibrary.org/works/{works_id}/ratings.json'
        works_response = requests.get(works_url)
        if works_response.status_code == 200:
            works_dict = works_response.json()
            rating = works_dict["summary"]["average"]
            if rating is None:
                return None
            else:
                return float(rating)
        else:
            return None
    else:
        return None       
    

def new_rating_function():
    rating_list = []
    nyt_dict = new_api_key()
    for item in nyt_dict:
        
        if item == None:
            continue
        else:
            rating = get_rating(item)
            if rating == None:
                continue
            else:
                get_values = nyt_dict.get(item)
                rating_list.append([item, get_values[0], get_values[1], get_values[2], rating])
    return rating_list


def set_up_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS Books (isbn13 INTEGER PRIMARY KEY, title TEXT UNIQUE, nyt_rank INTEGER, rating REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS Publishers (isbn13 INTEGER PRIMARY KEY, pub_id INTEGER)')
    return cur, conn

def set_up_tables(data, cur, conn):
    # get most recent count of things in the database
    # make api call but only take next 25 items to add to database
    for i in data:
        isbn13 = i[0]
        title = i[1]
        nyt_rank = i[2]
        pub_id = i[3]
        rating = i[4]
        cur.execute('INSERT OR IGNORE INTO Books(isbn13, title, nyt_rank, rating) VALUES (?,?,?,?)', (isbn13, title, nyt_rank, rating))
        cur.execute('INSERT OR IGNORE INTO Publishers(isbn13, pub_id) VALUES (?,?)', (isbn13, pub_id))
    conn.commit()

def analyze_data(cur, conn):
    cur.execute("ALTER TABLE Books ADD COLUMN new_rating REAL")
    rows = cur.execute("SELECT nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[0]
        rating = row[1]
        new_rating = nyt_rank + rating
        print(new_rating)
        cur.execute("INSERT INTO Books(new_rating) VALUES (?)", (new_rating,))
    conn.commit()

def main():
    cur, conn = set_up_database("Storage")
    data = new_rating_function()
    book_count = cur.execute('SELECT COUNT (*) FROM Books').fetchall()[0][0]

    if book_count < 1:
        first_25 = data[:25]
        set_up_tables(first_25, cur, conn)
        analyze_data(cur, conn)
    elif book_count < 26:
        next_25 = data[25:51]
        set_up_tables(next_25, cur, conn)
    elif book_count < 51:
        third_25 = data[51:76]
        set_up_tables(third_25, cur, conn)
    elif book_count < 76:
        last_25 = data[76:101]
        set_up_tables(last_25, cur, conn)

    conn.close()


main()

#data = new_rating_function()
#print(data)

# def get_isbn_numbers():
    # loop thru get book data and get isbn numbers for each book

# def get_open_library_book_data():
    # get book data based on isbn numbers for nyt books

# def set_up_database():

# def create_table():