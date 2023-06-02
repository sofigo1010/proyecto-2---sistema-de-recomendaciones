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
    #getCategorias
    def getCategorias(tx):
        result = tx.run('match (c: Categoria) return c.categoria')
        arrcategorias = []
        for record in result:
            arrcategorias.append(record["c.categoria"])
        
        #Se quitan los duplicados
        resultantList = []
 
        for element in arrcategorias:
            if element not in resultantList:
                resultantList.append(element)

        return resultantList

    
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


#se define la ruta del directorio
app = Flask(__name__, template_folder='C:\\Users\\andre\\OneDrive\\Desktop\\proyecto2-trabajosmax-main\\RTrabajosMaxRealFinal')#aqui se empieza a crear la aplicacion
neo4j = Neo4JExample('bolt://44.202.37.222:7687', 'neo4j', 'feed-sea-guide')


@app.route('/') #se define un temporador para la ruta principal '/login'


def inicio():

    return render_template('Index.html')

@app.route('/buscarTrabajosXCategoria', methods =['POST'])
def buscarTrabajoCategoria():
    categorias = request.form["Categoria"].split(",")  # Separamos las categorías por la coma
    listgetcategories = neo4j.callGetCategorias()
    arraytrabajos = []
    for categoria in categorias:
        realexiste = False
        for x in listgetcategories:
            if(categoria.lower().strip() == x.lower()):  # Usamos strip() para eliminar los espacios en blanco al inicio y al final
                realexiste = True
        if (realexiste):
            trabajos = neo4j.calltrabajosmatch(categoria)
            arraytrabajos.extend(trabajos)  # Agregamos los trabajos encontrados a la lista total
        else:
            return render_template('Buscaritas.html',flagError = True, mensaje = "Una o las categorias que buscaste no existe")
    return render_template('Buscaritas.html',busqueda = True, trabajos = arraytrabajos, realexiste=True)



@app.route('/verCategorias', methods =['POST'])
def verCategorias():
    listgetcategories = neo4j.callGetCategorias()    
    return render_template('Buscaritas.html', ver = True, categorias = listgetcategories)


@app.route('/agregarTrabajo', methods =['POST'])
def agregarTrabajo():
    categoria = request.form["Categoria"] 
    empresa = request.form["Empresa"] 
    puesto = request.form["Puesto"] 
    encargado = request.form["Encargado"] 
    valor = neo4j.callCreateNewJob(categoria, empresa, puesto, encargado)

    return render_template('Agregarreal.html', inserta = True)



@app.route('/Agregarreal', methods=['GET'])
def agregar():
    return render_template("Agregarreal.html")

@app.route('/buscar', methods=['GET'])
def buscar():
    return render_template('Buscaritas.html')

@app.route('/index', methods=['GET'])
def regresaralmain():
    return render_template('Index.html')



if __name__ == '__main__':
    #se inicia la aplicacion en modo debug
    app.run(debug=True)
