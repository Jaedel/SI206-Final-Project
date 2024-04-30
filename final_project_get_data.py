import requests
import sqlite3
import json
import os
import matplotlib
import matplotlib.pyplot as plt


NYT_API_KEY = 'Y4YC23d1jbw0W2Y9pu5NgxFWFm1Mrz8p'

def new_api_key():
    '''
    This function makes a request to The New York Times
    Bestsellers List for 4/1/22. The function then checks
    and ensures that the response.status_code == 200 and 
    loads the data as a json file. After, it loops through
    the specific genre lists and finds information about the
    isbn number, title, rank, and publisher for each book. 
    To avoid duplicate titles, it adds each title to a title
    dictionary and makes sure to only get information from a
    book if the title isn’t already in the dictionary. This function
    creates a publisher ID key by creating a publisher dictionary
    and checking if the publisher is already in the dictionary.
    The keys of this dictionary are the publisher name and the
    values are a publisher id created by the publisher variable.
    If the publisher name is already in the publisher dictionary,
    it assigns the publisher id number value to the new_dict publisher
    id value. If the publisher name is not already in the dictionary,
    it adds it to the dictionary and increments publisher so that
    there is a new publisher id that can be added as the value in new_dict. 
    INPUTS: 
        none

    OUTPUTS: 
        new_dict: dictionary with primary isbn13 number as the key, and title,
        rank on the NYT Bestsellers list, and publisher ID as the values
    '''
    new_dict = {}
    publisher_dict = {}
    title_dict = {}
    num_value = 0
    publisher = 0
    published_date = '2022-04-01'
    response = requests.get(url=f'https://api.nytimes.com/svc/books/v3/lists/full-overview.json?published_date={published_date}&api-key={NYT_API_KEY}')
    if response.status_code == 200:
        data = json.loads(response.text)
        for item in data["results"]["lists"]:
            for i in item["books"]:
                if i["title"] not in title_dict.keys():
                    title_dict[i["title"]] = 1
                    if i["publisher"] not in publisher_dict.keys():
                        num_value += 1
                        publisher_dict[i["publisher"]] = num_value
                    publisher = publisher_dict[i["publisher"]]
                    new_dict[i["primary_isbn13"]] = [i["title"], i["rank"], publisher]              
    return new_dict

def get_rating(isbn):
    '''
    This function makes a request to the Open Library API ISBN page for a specific book based on the ISBN number,
    which is taken as an argumnet for this function. After ensuring the request is successfully stored to a variable,
    it takes the works value from the json so that another request can be made to open up the works page for that same book.
    From there it then ensures the request is successfully stored to a variable, stores the rating for the book by searching
    through the JSON (first checking if it exists and returning None if it doesn't), and returns the rating as a float.

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
    '''
    This function first gets all the data from the new_api_key()
    function which returns a dictionary with isbn number as the 
    key and title, rank on NYT Bestsellers list, and publisher id
    as the values. It then loops through the keys of that dictionary
    (which are the isbn numbers) and for each isbn number, it finds 
    the Open Library rating using the get_rating() function. If the
    isbn number provided by the new_api_key() function is ‘None’, do
    not find the Open Library rating because it needs an isbn number
    to work properly. Check to see if the isbn number has a corresponding
    rating on Open Library, and if it does, create a list with isbn number,
    book title, rank on NYT Bestsellers list, publisher if, and Open Library rating.
    Add this list to the rating_list so that the output is a list of lists. 

    INPUTS: 
        none 

    OUTPUTS: 
        rating_list: list with isbn number, book title,
        rank on New York Times Bestsellers list,
        publisher id, and Open Library rating
    '''
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
    '''
    This function establishes a path and file for the database using the name that is input as the argument.
    This then creates the connection and cursor objects for the database. Afterwards, two tables are then created
    so that data on Books can then be inserted into these tables for future calculations.
    
    ARGUMENTS: 
        title: Name of the database 

    RETURNS: 
        The database's cursor and connection objects
    '''
    
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS Books (isbn13 INTEGER PRIMARY KEY, title TEXT, nyt_rank INTEGER, rating REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS Publishers (isbn13 INTEGER PRIMARY KEY, pub_id INTEGER)')
    return cur, conn

def set_up_tables(data, cur, conn):
    '''
    This function takes the name of the database, cursor object for the database, and connection object for the database as arguments.
    The function then loops through each row of the database and inserts data into two tables. The first table takes the following
    values: isbn13, title, NYT rank, rating. The second table takes the following values: isbn13 and Publisher ID. The function also
    commits this inserted data for each row each time the loop is run.
    
    ARGUMENTS: 
        title: Name of the database, cursor object for the database, connection object for the database

    RETURNS: 
        No return
    '''

    for i in data:
        isbn13 = i[0]
        title = i[1]
        nyt_rank = i[2]
        pub_id = i[3]
        rating = i[4]
        cur.execute('INSERT OR IGNORE INTO Books(isbn13, title, nyt_rank, rating) VALUES (?,?,?,?)', (isbn13, title, nyt_rank, rating))
        cur.execute('INSERT OR IGNORE INTO Publishers(isbn13, pub_id) VALUES (?,?)', (isbn13, pub_id))
        conn.commit()


def analyze_first_data(cur, conn):
    '''
    This function adds a new column called new_rating to
    the Books Table. Then it gets the isbn13, nyt_rank_ and rating
    from the Books Table. For each isbn number, calculate a new rating
    (called new_rating) which subtracts the NYT_rank from Open
    Library rating. Then, for each isbn number, add the new_rating calculation to
    the new_rating column in the Books Table. 
    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    cur.execute("ALTER TABLE Books ADD COLUMN new_rating REAL")
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = rating - nyt_rank
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def analyze_data(cur, conn):
    '''
    This function gets the isbn13, nyt_rank_ and rating
    from the Books Table. For each isbn number, calculate a new rating
    (called new_rating) which subtracts the NYT_rank from Open
    Library rating. Then, for each isbn number, add the new_rating calculation to
    the new_rating column in the Books Table. 

    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = rating - nyt_rank
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def create_first_visualization(cur, conn):
    '''
    This function creates a bar chart that displays the
    title and the new_rating for the Top 5 Books based on the new_rating
    in our database. First, this function creates a title list and a rating list
    for the x and y axes, respectively. It also creates a list for the widths
    so that each width is 0.3 on the chart is 0.3. After, this function gets the title and
    new_rating from the Books Table and these should be in descending order because the
    larger the rating, the better the score is for our metric. Then, the function should
    loop through each new_rating for its respective title and only add the title and
    rating to the title_list and rating_list for the top 5 books. If the book title is longer
    than 10 letters, only add a string with the first 10 letters and ‘..’ Create a bar chart
    with the x label as ’Book Title (First 10 Letters) and y label as (New Rating
    Calculation). The chart title should be ‘New Rating Calculation for Top 5 Books’)
    And it should be saved as an image. 


    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    
    title_list = []
    rating_list = []
    widths = [0.3, 0.3, 0.3, 0.3, 0.3]
    items = cur.execute('SELECT title, new_rating FROM Books ORDER BY new_rating DESC').fetchall()
    count = 0
    for item in items:
        if count < 5:
            count += 1
            book_title = item[0]
            if len(book_title) > 10:
                first_ten_characters = book_title[:11] + '..'
                title_list.append(first_ten_characters)
            else:
                title_list.append(book_title)
            rating_list.append(item[1])
        else:
            break
    plt.bar(title_list, rating_list, color='red', width= widths) 
    plt.xlabel("Book Title (First 10 Letters)") 
    plt.ylabel("New Rating Calculation")  
    plt.title("New Rating Calculation for Top 5 Books") 
    plt.savefig("barchart_newrating_and_title.png")
    plt.show()
    conn.commit()

def create_second_visualization(cur, conn):
    '''
    This function gets the isbn13, nyt_rank_ and rating
    from the Books Table. For each isbn number, calculate a new rating
    (called new_rating) which subtracts the NYT_rank from Open
    Library rating. Then, for each isbn number, add the new_rating calculation to
    the new_rating column in the Books Table. 

    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''

    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = rating - nyt_rank
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def create_first_visualization(cur, conn):
    '''
     This function creates a JOIN statement based on the isbn number for
     each book in the Books and Publishers tables. It gets the publisher id
     and new_rating for each isbn number. Then it loops through the publisher
     id and rating for each book and checks if the publisher id is in the
     pub_dict. If it is, it adds the new_rating to the list of values. If not,
     it creates a new key in the pub_dict dictionary and assigns that rating as
     a value which should be a list. Then it loops through the pub_dict dictionary
     to determine which keys have values with lists greater than 2 items in the.
     If the value for a specified key has more than 2 items, it adds that key and value
     pair to a new dictionary called new_dict. then loop through the new_dict dictionary to create two
     lists for the x and y axis. For each new_rating in the new_dict add the publisher id to the an axis
     list and the new_rating to the y axis list (be sure to add the publisher id for each individual new_rating in the list).
     Then, plot the x and y lists as a scatterplot using x label ‘New Ratings for Publisher’s Books’ and y label
     ‘New Rating Calculations for 5 Publishers’. Make sure create a new list for x axis tick labels so that it
     increments in counts of 3’s. Also, chart should be saved as an image. 

    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    pub_dict = {}
    new_dict = {}

    rows = cur.execute('SELECT Publishers.pub_id, Books.new_rating FROM Publishers JOIN Books ON Publishers.isbn13 = Books.isbn13').fetchall()
    for row in rows:
        pub_id = row[0]
        rating = row[1]
        if pub_id in pub_dict.keys():
            pub_dict[pub_id].append(rating)
        else:
            pub_dict[pub_id] = [rating]

    for pub in pub_dict.keys():
        if len(pub_dict.get(pub)) > 2:
            vals_of_pub = pub_dict[pub]
            new_dict[pub] = vals_of_pub
        else:
            continue

    count = 0

    x_axis_list = []
    y_axis_list = []
    x_tick_labels = []
    axis_count = 0

    for i in new_dict.keys():
        if count < 5:
            count += 1
            for val in new_dict.get(i):
                x_axis_list.append(i)
                individual_value = val
                y_axis_list.append(individual_value)
        else:
            break

    while axis_count < 51:
        axis_count += 3
        x_tick_labels.append(axis_count)

    ax = plt.axes()
    plt.scatter(x_axis_list, y_axis_list) 
    ax.set_xticks(x_tick_labels)
    plt.grid()
    plt.xlabel("Publisher ID") 
    plt.ylabel("New Ratings for Publisher's Books")  
    plt.title("New Rating Calculations for 5 Publishers") 
    plt.savefig("scatterplot_newrating_and_publisher.png")
    plt.show()
    conn.commit()


def main():
    '''
    This function is the main function of the program where most other functions are called. It takes no arguments.
    This function first creates the database, assigning it the name of "Storage" and assiging the cursor and connection
    objects to variables. Next it calls the new_rating_function() to add the new ratings to the database, after which
    it then stores this database to a variable called data. Following this, the current number of books within the Books
    table is stored into a variable. Following this, data is inserted into the Books and Publishers tables within the
    database, 25 books at a time. This is done by checking how many books are already added into the Books table, and
    inserting data for the next 25 books based on that value. If the code is run and the book count is above 76 and
    below 101 this means that the database has been populated with 100 items total, and so the visualizations are
    then made. This is done by calling each function for each visualization. Lastly, this function always closes the connection object.
    
    ARGUMENTS: 
        No arguments

    RETURNS: 
        No return
    '''
    cur, conn = set_up_database("Storage")
    data = new_rating_function()
    book_count = cur.execute('SELECT COUNT (*) FROM Books').fetchall()[0][0]
    

    if book_count < 1:
        first_25 = data[:25]
        set_up_tables(first_25, cur, conn)
        analyze_first_data(cur, conn)
    elif book_count < 26:
        next_25 = data[25:50]
        set_up_tables(next_25, cur, conn)
        analyze_data(cur, conn)
    elif book_count < 51:
        third_25 = data[50:75]
        set_up_tables(third_25, cur, conn)
        analyze_data(cur, conn)
    elif book_count < 76:
        last_25 = data[75:100]
        set_up_tables(last_25, cur, conn)
        analyze_data(cur, conn)

    elif book_count < 101:
        create_first_visualization(cur, conn)
        create_second_visualization(cur, conn)

    conn.close()

main()