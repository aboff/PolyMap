import mysql.connector
from mysql.connector import Error
import json
with open('settings.json') as f:
	settings = json.load(f)

data = []

def loadData():
	try:
		connexion = mysql.connector.connect(
			host=settings["db"]["host"],
			user=settings["db"]["user"],
			password=settings["db"]["password"],
			database=settings["db"]["database"],
			port=settings["db"]["port"]
		)

		#request = "select p1.label, p2.label from people p1 left join relationships r on p1.id = r.person1 left join people p2 on r.person2 = p2.id where p2.id is not null"
		request = "select p1.id, p1.label from people p1 "
		curseur = connexion.cursor()
		curseur.execute(request)

		relations = curseur.fetchall()

		for relation in relations:
			print(relation)
			subrequest = "select person2 from relationships where person1 = " + str(relation[0])
			curseur.execute(subrequest)
			nodesTo = curseur.fetchall()
			subrequest = "select person1 from relationships where person2 = " + str(relation[0])
			curseur.execute(subrequest)
			nodesFrom = curseur.fetchall()
			print(nodesTo)
			data.append({
				'ID': relation[0],
				'data' : {
					'title':relation[1]
				},
				'nodesTo' : nodesTo,
				'nodesFrom' : nodesFrom
			})

	except Error as e:
		print("Exception : ", e)

	finally:
		if(connexion.is_connected()):
			connexion.close()
			curseur.close()

#		with open('data.json', 'w') as outfile:
#			json.dump(data,outfile,indent=4)


import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/data.json', methods=['GET'])
def api_all():
	loadData()
	return jsonify(data)

app.run()