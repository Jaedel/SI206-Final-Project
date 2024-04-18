import requests
import sqlite3
import json
import os

NYT_API_KEY = 'Y4YC23d1jbw0W2Y9pu5NgxFWFm1Mrz8p'

def new_api_key():
    new_dict = {}
    
    published_date = '2022-04-01'
    response = requests.get(url=f'https://api.nytimes.com/svc/books/v3/lists/full-overview.json?published_date={published_date}&api-key={NYT_API_KEY}')
    if response.status_code == 200:
        data = json.loads(response.text)
        for item in data["results"]["lists"]:
            for i in item["books"]:
                new_dict[i["primary_isbn13"]] = [i["title"], i["rank"], i["publisher"]]
    return new_dict

data = new_api_key()
print(len(data.keys()))

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
    count = 0
    rating_dict = {}
    while count < 101:
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
                    rating_dict[item] = [get_values[0], get_values[1], get_values[2], rating]
                    count += 1
    return rating_dict


def set_up_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    return cur, conn

def set_up_general_table(cur, conn):
    data = new_rating_function()
    cur.execute('CREATE TABLE IF NOT EXISTS Books (isbn13 INTEGER PRIMARY KEY, title TEXT UNIQUE, nyt_rank INTEGER, publisher TEXT, rating REAL)')
    for i in data:
        isbn13 = i
        title = data[i][0]
        nyt_rank = data[i][1]
        publisher = data[i][2]
        rating = data[i][3]
        cur.execute('INSERT INTO Books(isbn13, title, nyt_rank, publisher, rating) VALUES (?,?,?,?.?)', (isbn13, title, nyt_rank, publisher, rating))

    conn.commit()

cur, conn = set_up_database("Storage")
set_up_general_table(cur, conn)
conn.close()


#data = new_rating_function()
#print(data)

# def get_isbn_numbers():
    # loop thru get book data and get isbn numbers for each book

# def get_open_library_book_data():
    # get book data based on isbn numbers for nyt books

# def set_up_database():

# def create_table():