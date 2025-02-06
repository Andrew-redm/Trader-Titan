from SPARQLWrapper import SPARQLWrapper, JSON

def fetch_dbpedia_data(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def fetch_cities_population(limit=10, min_population=1000000, min_wikilinks=1000, max_page_id=10000000):
    #make the questions less shit
    query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?city ?cityName ?population (COUNT(?link) AS ?wikilinkCount) ?pageID
        WHERE {{
            ?city a dbpedia-owl:City ;
                  rdfs:label ?cityName ;
                  dbpedia-owl:populationTotal ?population ;
                  dbo:wikiPageWikiLink ?link;
                  dbo:wikiPageID ?pageID.
            FILTER(LANG(?cityName) = "en")
            FILTER (?population > {min_population})
            FILTER (?pageID < {max_page_id})
        }}
        GROUP BY ?city ?cityName ?population ?pageID
        HAVING (COUNT(?link) > {min_wikilinks})
        ORDER BY RAND()
        LIMIT {limit}
    """
    return fetch_dbpedia_data(query)

def fetch_rivers_length(limit=10, min_length=500000, min_wikilinks=500, max_page_id=5000000):
    query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?river ?riverName ?length (COUNT(?link) AS ?wikilinkCount) ?pageID
        WHERE {{
            ?river a dbpedia-owl:River ;
                   rdfs:label ?riverName ;
                   dbpedia-owl:length ?length ;
                   dbo:wikiPageWikiLink ?link;
                   dbo:wikiPageID ?pageID.
            FILTER(LANG(?riverName) = "en")
            FILTER (?length > {min_length})
            FILTER (?pageID < {max_page_id})
        }}
        GROUP BY ?river ?riverName ?length ?pageID
        HAVING (COUNT(?link) > {min_wikilinks})
        ORDER BY RAND()
        LIMIT {limit}
    """
    return fetch_dbpedia_data(query)

def fetch_mountains_elevation(limit=10, min_elevation=3000, min_wikilinks=200, max_page_id=8000000):
    query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?mountain ?mountainName ?elevation (COUNT(?link) AS ?wikilinkCount) ?pageID
        WHERE {{
            ?mountain a dbpedia-owl:Mountain ;
                      rdfs:label ?mountainName ;
                      dbpedia-owl:elevation ?elevation;
                      dbo:wikiPageWikiLink ?link;
                      dbo:wikiPageID ?pageID.
            FILTER(LANG(?mountainName) = "en")
            FILTER (?elevation > {min_elevation})
            FILTER (?pageID < {max_page_id})
        }}
        GROUP BY ?mountain ?mountainName ?elevation ?pageID
        HAVING (COUNT(?link) > {min_wikilinks})
        ORDER BY RAND()
        LIMIT {limit}
     """
    return fetch_dbpedia_data(query)

def fetch_companies_employees(limit=10, min_employees=10000, min_wikilinks=500, max_page_id=10000000):
      query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?company ?companyName ?employees (COUNT(?link) AS ?wikilinkCount) ?pageID
        WHERE {{
           ?company a dbpedia-owl:Company ;
                    rdfs:label ?companyName ;
                    dbpedia-owl:numberOfEmployees ?employees ;
                    dbo:wikiPageWikiLink ?link;
                    dbo:wikiPageID ?pageID.
           FILTER(LANG(?companyName) = "en")
           FILTER (?employees > {min_employees})
           FILTER (?pageID < {max_page_id})
        }}
        GROUP BY ?company ?companyName ?employees ?pageID
        HAVING (COUNT(?link) > {min_wikilinks})
        ORDER BY RAND()
        LIMIT {limit}
      """
      return fetch_dbpedia_data(query)