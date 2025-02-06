import mysql.connector
import os
from dotenv import load_dotenv
from dbpedia_utils import fetch_cities_population, fetch_rivers_length, fetch_mountains_elevation, fetch_companies_employees
import random

load_dotenv()

def populate_database():
    db_host = os.environ.get('MYSQL_HOST')
    db_user = os.environ.get('MYSQL_USER')
    db_password = os.environ.get('MYSQL_PASSWORD')
    db_name = os.environ.get('MYSQL_DATABASE')

    conn = None
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()

        cities = fetch_cities_population(limit=5)
        rivers = fetch_rivers_length(limit=5)
        mountains = fetch_mountains_elevation(limit=5)
        companies = fetch_companies_employees(limit=5)
        all_data = []

        question_templates = [
          "What is the {property} of {entity}?",
          "The {property} of {entity} is what?",
          "How {property_adj} is {entity}?"
        ]

        if cities:
          for city in cities:
            try:
                city_name = city['cityName']['value']
                population = int(city['population']['value'])

                if population > 0:
                  question = random.choice(question_templates).format(property='population', entity=city_name, property_adj='large')
                  all_data.append((question, population, 'people', 'population,city'))
            except (ValueError, TypeError):
                continue

        if rivers:
            for river in rivers:
              try:
                river_name = river['riverName']['value']
                length_meters = float(river['length']['value'])
                length_km = length_meters / 1000 

                if length_km > 1:
                    question = random.choice(question_templates).format(property="length", entity=river_name, property_adj='long')
                    all_data.append((question, length_km, 'km', 'length,river'))
              except (ValueError, TypeError):
                continue
        
        if mountains:
           for mountain in mountains:
              try:
                 mountain_name = mountain['mountainName']['value']
                 elevation = float(mountain['elevation']['value'])

                 if elevation > 0:
                  question = random.choice(question_templates).format(property='elevation', entity = mountain_name, property_adj='high')
                  all_data.append((question, elevation, 'meters', 'elevation,mountain'))
              except (ValueError, TypeError):
                continue
        
        if companies:
           for company in companies:
              try:
                 company_name = company['companyName']['value']
                 num_employees = int(company['employees']['value'])

                 if num_employees > 0:
                    question = random.choice(question_templates).format(property='number of employees', entity = company_name, property_adj='many employees')
                    all_data.append((question, num_employees, 'employees', 'employees,company'))
              except (ValueError, TypeError):
                continue
        
        random.shuffle(all_data)

        added_count = 0
        for question, answer, units, tags in all_data:
            # Check for duplicates
            cursor.execute("SELECT id FROM questions WHERE question = %s", (question,))
            if not cursor.fetchone():  
                cursor.execute("INSERT INTO questions (question, answer, units, tags) VALUES (%s, %s, %s, %s)",
                               (question, answer, units, tags))
                added_count += 1

        conn.commit()
        print(f"Added {added_count} questions to the database.")

    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == '__main__':
    populate_database()