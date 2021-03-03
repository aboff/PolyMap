import os
import sys
import mysql.connector
from mysql.connector import Error
import json
with open('settings.json') as f:
	settings = json.load(f)

from flask import Flask, redirect, url_for,request, jsonify, session, g, abort
from requests_oauthlib import OAuth2Session


app = Flask(__name__)
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
OAUTH2_CLIENT_ID =  app.config["DISCORD_CLIENT_ID"] = settings["oauth"]["clientId"]
OAUTH2_REDIRECT_URI  = app.config["DISCORD_REDIRECT_URI"] = settings["callbackUrl"]
DISCORD_GUILD_ID = settings['discordGuild']
BASE_URL = settings["baseUrl"]

if 'http://' not in OAUTH2_REDIRECT_URI:
	os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

app.config["APPLICATION_ROOT"] = "/api/"
OAUTH2_CLIENT_SECRET = app.config["DISCORD_CLIENT_SECRET"] = settings["oauth"]["clientSecret"]
app.config["DISCORD_BOT_TOKEN"] = ""                    # Required to access BOT resources.
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
app.config["SESSION_COOKIE_NAME"]="PolyMap"
app.config["TESTING"] = True
app.config["DEBUG"] = True

def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

data = []

def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False

def loadData():
	try:
		connexion = mysql.connector.connect(
			host=settings["db"]["host"],
			user=settings["db"]["user"],
			password=settings["db"]["password"],
			database=settings["db"]["database"],
			port=settings["db"]["port"]
		)

		request = "select p1.id, p1.label from people p1 "
		curseur = connexion.cursor()
		curseur.execute(request)

		relations = curseur.fetchall()

		for relation in relations:
			print("relation : ", relation)
			subrequest = "select person2 from relationships where person1 = " + str(relation[0])
			curseur.execute(subrequest)
			nodesTo = curseur.fetchall()
			subrequest = "select person1 from relationships where person2 = " + str(relation[0])
			curseur.execute(subrequest)
			nodesFrom = curseur.fetchall()
			print("nodesTo : ", nodesTo)
			print("nodesFrom : ", nodesFrom)
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

@app.route('/data.json', methods=['GET'])
def api_all():
	if "oauth2_token" not in session:
		abort(401)
	else:
		discord = make_session(token=session.get('oauth2_token'))
		user = discord.get(API_BASE_URL + '/users/@me').json()
		guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
		print( "DISCORD_GUILD_ID", DISCORD_GUILD_ID)
		print("guilds: ", guilds)
		print(type(guilds))

		if contains(guilds, lambda x: x['id'] == DISCORD_GUILD_ID):
			loadData()
		else:
			abort(403)
	return jsonify(data)

@app.route('/login')
@app.route('/')
def index():
	if "oauth2_token" in session:
		return redirect(BASE_URL)
	else:
	    scope = request.args.get('scope','identify guilds')
	    discord = make_session(scope=scope.split(' '))
	    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
	    session['oauth2_state'] = state
	    return redirect(authorization_url)


@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(BASE_URL)

@app.route('/logout')
def logout():
	try:
		session.clear()
	finally:
		return redirect(BASE_URL)

if __name__ == "__main__":
    app.run()