import psycopg2
import bigjson
import ijson


def connect():
    try:
        conn = psycopg2.connect("dbname=pubmed user=postgres password=postgres")
        cur = conn.cursor()
        cur.execute("SELECT version()")
        db_version = cur.fetchone()
        print("yeah",db_version)
        cur.close()
    except Exception as e:
        print("FUCK ", e)
    finally:
        if conn is not None:
            conn.close()
            print("DataBase connection closed")
def add_data_to_database(filepath):
    with open(filepath, 'rb') as f:
        objects = ijson.items(f,'')
        for o in objects:
            print(o)
        #j = bigjson.load(f)
        #element = j[]
        #print(element['type'])

if __name__ == "__main__":
    connect()
    add_data_to_database("../pubmed_search_results.json")
