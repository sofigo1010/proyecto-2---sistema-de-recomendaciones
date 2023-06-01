from flask import Flask, request, render_template
from neo4j import GraphDatabase, basic_auth
import json

class Neo4JExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth= basic_auth(user, password))

    def close(self):
        self.driver.close()
    
    def callCreateNewJob(self, categoria, empresa, puesto, encargado):
        with self.driver.session(database="neo4j") as session:
            entrada = session.write_transaction(self.createNewJob, categoria, empresa, puesto, encargado)
        return entrada
    
    def callGetCategorias(self):
        with self.driver.session(database="neo4j") as session:
            entrada = session.read_transaction(self.getCategorias)
        return entrada

    def countNodes(self):
        cypher_query = '''
        MATCH (n)
        RETURN COUNT(n) AS count
        LIMIT $limit
        '''
        with self.driver.session(database="neo4j") as session:
            results = session.read_transaction(
                lambda tx: tx.run(cypher_query,
                                limit=100).data())
            for record in results:
                print(record['count'])
    
    def calltrabajosmatch(self,categoria):
        with self.driver.session() as session:
            entrada = session.execute_write(self.trabajosmatch, categoria)
        return entrada
    
    @staticmethod
    def trabajosmatch(tx, categoria):
        resultado = tx.run("""
            MATCH (cat:Categoria {categoria: $categoria})<-[:Categoria_de]-(e:Empresa)-[:Encargado_de]->(enc:Encargado), (e)-[:Puesto_disponible]->(p:Puesto) 
            RETURN e.name AS Empresa, p.name AS Puesto, enc.name AS Encargado
            """, categoria=categoria)
        trabajos = []
        for record in resultado:
            trabajos.append([
                "Empresa: " + record["Empresa"],
                "Puesto: " + record["Puesto"],
                "Encargado: " + record["Encargado"]
            ])
        return trabajos



    
    @staticmethod
    def createNewJob(tx, categoria, empresa, puesto, encargado):
        tx.run("CREATE (:Categoria {categoria: $categoria})", categoria=categoria)
        tx.run("CREATE (:Empresa {name: $empresa})", empresa=empresa)
        tx.run("CREATE (:Puesto {name: $puesto})", puesto=puesto)
        tx.run("CREATE (:Encargado {name: $encargado})", encargado=encargado)
        tx.run("""
            MATCH (c:Categoria {categoria: $categoria}), (e:Empresa {name: $empresa})
            CREATE (e)-[:Categoria_de]->(c)
            """, categoria=categoria, empresa=empresa)
        tx.run("""
            MATCH (e:Empresa {name: $empresa}), (p:Puesto {name: $puesto})
            CREATE (e)-[:Puesto_disponible]->(p)
            """, empresa=empresa, puesto=puesto)
        tx.run("""
            MATCH (e:Empresa {name: $empresa}), (en:Encargado {name: $encargado})
            CREATE (e)-[:Encargado_de]->(en)
            """, empresa=empresa, encargado=encargado)
    
neo4j = Neo4JExample('bolt://18.212.169.121:7687', 'neo4j', 'lungs-binder-videos')
print (neo4j.calltrabajosmatch("Bebidas"))