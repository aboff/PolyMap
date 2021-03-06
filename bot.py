# import sys
import mysql.connector
from mysql.connector import Error
import json
with open('settings.json') as f:
	settings = json.load(f)
discordBotToken= settings["discordBotToken"]                    # Required to access BOT resources.
siteUrl = settings["baseUrl"]
discordBotChannelId = settings["discordBotChannel"]
discordBotLogChannelId = settings["discordBotLogChannel"]
deleteDelay = settings["deleteBotChannelMessageDelay"]
discordBotOwnerId = settings["discordBotOwner"]

import discord
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

async def createRelationship(person1, person2):
	
	request = "SELECT id from people WHERE discordTag='{0}#{1}'".format(person1.name, person1.discriminator)
	person1SQLId = await executeSQLRequestWithSingleResult(request)
	# print("person1SQLId: {0}".format(person1SQLId))
	if not person1SQLId:
		request = "INSERT INTO people(label, discordTag) Values('{0}', '{1}#{2}') ON DUPLICATE KEY UPDATE label='{0}'".format(person1.name, person1.name, person1.discriminator)
		person1SQLId = await executeSQLRequestWithoutResult(request)
		# print("person1SQLId : {0}".format(person1SQLId))
		# print("trying to insert {0} in DB -> id found: {1}".format(person1, person1SQLId))

	request = "SELECT id from people WHERE discordTag='{0}#{1}'".format(person2.name, person2.discriminator)
	person2SQLId = await executeSQLRequestWithSingleResult(request)
	# print("person2SQLId: {0}".format(person2SQLId))
	if not person2SQLId:
		request = "INSERT INTO people(label, discordTag) Values('{0}', '{1}#{2}') ON DUPLICATE KEY UPDATE label='{0}'".format(person2.name, person2.name, person2.discriminator)
		person2SQLId = await executeSQLRequestWithoutResult(request)
		# print("person2SQLId: {0}".format(person2SQLId))
	# print("trying to insert {0} in DB -> id found: {1}".format(person2, person2SQLId))

	request = "INSERT INTO relationships(person1, person2) Values({0}, {1})".format(person1SQLId, person2SQLId)
	# print("request: {0}".format(request))
	await executeSQLRequestWithoutResult(request)

async def sendBotOwnerMP(message):
	discordBotOwner = client.get_user(discordBotOwnerId)
	await discordBotOwner.send(message)

async def executeSQLRequestWithListResult(request):
	try:
		connexion = mysql.connector.connect(
			host=settings["db"]["host"],
			user=settings["db"]["user"],
			password=settings["db"]["password"],
			database=settings["db"]["database"],
			port=settings["db"]["port"],
			auth_plugin='mysql_native_password',
			autocommit=True
		)

		curseur = connexion.cursor()
		curseur.execute(request)

		return curseur.fetchall()

	except Error as e:
		await log("Doh ! J'arrive pas à accéder à la base de données \U0001F635")
		await sendBotOwnerMP("Exception : {0}\nRequest : {1}".format(e, request))

	finally:
		if(connexion.is_connected()):
			connexion.close()
			curseur.close()

async def executeSQLRequestWithSingleResult(request):
	try:
		connexion = mysql.connector.connect(
			host=settings["db"]["host"],
			user=settings["db"]["user"],
			password=settings["db"]["password"],
			database=settings["db"]["database"],
			port=settings["db"]["port"],
			auth_plugin='mysql_native_password',
			autocommit=True
		)
		curseur = connexion.cursor()
		curseur.execute(request)

		return curseur.fetchone()[0]

	except Error as e:
		await log("Doh ! J'arrive pas à accéder à la base de données \U0001F635")
		await sendBotOwnerMP("Exception : {0}\nRequest : {1}".format(e, request))

	finally:
		if(connexion.is_connected()):
			connexion.close()
			curseur.close()

async def executeSQLRequestWithoutResult(request):
	try:
		connexion = mysql.connector.connect(
			host=settings["db"]["host"],
			user=settings["db"]["user"],
			password=settings["db"]["password"],
			database=settings["db"]["database"],
			port=settings["db"]["port"],
			auth_plugin='mysql_native_password',
			autocommit=True
		)

		curseur = connexion.cursor()
		curseur.execute(request)
		return curseur.lastrowid

	except Error as e:
		await log("Doh ! J'ai des soucis la base de données \U0001F635")
		await sendBotOwnerMP("Exception : {0}\nRequest : {1}".format(e, request))

	finally:
		if(connexion.is_connected()):
			connexion.close()
			curseur.close()


async def purge(dmchannel):
	async for msg in dmchannel.history(limit=100):
		if msg.author == client.user: #client.user or bot.user according to what you have named it
			await msg.delete()

async def log(entry):
	discordBotLogChannel = client.get_channel(discordBotLogChannelId)
	await discordBotLogChannel.send(entry)

async def purgeCommandChan():
	discordBotChannel = client.get_channel(discordBotChannelId)
	async for msg in discordBotChannel.history(limit=100):
		await msg.delete()
	await discordBotChannel.send("Bonjour ! Pour déclarer une relation sur {0} il vous suffit de tagger la personne sur ce chan. La relation sera ajoutée dès qu'elle aura été validée (NON FONCTIONNEL POUR LE MOMENT)".format(siteUrl))

async def testDM(message):
	history = await message.channel.history(limit=10).flatten()
	if len(history) == 1:
		await message.reply('Oh {0}, un MP ! Je suis honnoré !'.format(message.author.mention))
	elif message.content == '!purge':
		await purge(message.channel)

@client.event
async def on_ready():
	await purgeCommandChan()
	print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if isinstance(message.channel, discord.channel.DMChannel):
    	await testDM(message)

    if message.content.startswith('$hello'):
        await message.reply('Hello ' + message.author.mention + ' ! (' + str(message.channel) + ')')

    if message.channel.id == discordBotChannelId:
    	if message.author != client.user:
    		await message.delete(delay=deleteDelay)

    	if message.mentions is not None and not message.reference:
    		for index, value in enumerate(message.mentions):
    			if value != message.author and value != client.user:
    				request = """select 'toto' from relationships r left join people p1 on r.person1 = p1.id join people p2 on r.person2 = p2.id where (p1.discordTag="{0}#{1}" and p2.discordTag="{2}#{3}") or (p2.discordTag="{0}#{1}" and p1.discordTag="{2}#{3}")""".format(message.author.name, message.author.discriminator, value.name, value.discriminator) #curseur.execute(subrequest)
    				relationships = await executeSQLRequestWithListResult(request)
    				if not relationships:
	    				reply = await message.reply("\U00002764 \U00002753 {0} a déclaré être en relation avec {1}. Pour ajouter cette relation à {2} merci de réagir avec \U0001F44D. Sinon, merci d'utiliser \U0001F44E".format(message.author.mention, value.mention, siteUrl))
	    				await reply.add_reaction('\U0001F44D')
	    				await reply.add_reaction('\U0001F44E')
	    			else:
	    				reply = await message.reply("\U0001F494 \U00002753 {0} a déclaré ne plus être en relation avec {1}. Pour retirer cette relation de {2} merci de réagir avec \U0001F494. Pour annuler, merci d'utiliser \U0001F645".format(message.author.mention, value.mention, siteUrl))
	    				await reply.add_reaction('\U0001F494')
	    				await reply.add_reaction('\U0001F645')

@client.event
async def on_reaction_add(reaction, user):
	if user == client.user:
		return
	if  reaction.message.channel.id == discordBotChannelId:
		# await reaction.message.channel.send(user.mention + " a réagi avec " + reaction.emoji)
		originalAuthor = client.user if reaction.message.author != client.user or not reaction.message.reference else reaction.message.reference.cached_message.author

		if reaction.message.mentions is not None:
			for index, value in enumerate(reaction.message.mentions):
				if value != client.user and value != originalAuthor:
					if reaction.emoji =='\U0001F44D' and value != originalAuthor and value != client.user and value == user:
						reply = await reaction.message.channel.send("Rhooo c'est trop mignon !")
						await createRelationship(originalAuthor, value)
						await log("{0} a déclaré une relation avec {1}. La relation vient d'être validée par {1}".format(originalAuthor, user))
						await reaction.message.delete()
						await reply.delete(delay=10)
					if reaction.emoji =='\U0001F44E' and value != originalAuthor and value != client.user and value == user:
						reply = await reaction.message.channel.send("Ah... dommage !")
						await log("{0} a voulu déclarer une relation avec {1}, mais s'est pris un rateau.".format(originalAuthor, user))
						await reaction.message.delete()
						await reply.delete(delay=10)
					if reaction.emoji =='\U0001F645' and value != client.user and (user == originalAuthor or value == user):
						await reaction.message.delete()
					if reaction.emoji =='\U0001F494' and value != client.user and (user == originalAuthor or value == user):
						reply = await reaction.message.channel.send("\U0001FAC2")
						request = "DELETE r FROM relationships r LEFT JOIN people p1 ON r.person1 = p1.id LEFT JOIN people p2 ON r.person2 = p2.id WHERE (p1.discordTag='{0}#{1}' AND p2.discordTag='{2}#{3}') OR (p2.discordTag='{0}#{1}' AND p1.discordTag='{2}#{3}')".format(originalAuthor.name, originalAuthor.discriminator, value.name, value.discriminator)
						await executeSQLRequestWithoutResult(request)
						await log("{0} a déclaré la fin de sa relation avec {1}. La fin de relation vient d'être validée par {2}".format(originalAuthor, value, user))
						await reaction.message.delete()
						await reply.delete(delay=10)

@client.event
async def on_member_update(before, after):
	origin = before.name if not before.nick else before.nick
	dest = after.name if not after.nick else after.nick
	if origin != dest:
		await log("{2}#{3}: {0} s'appelle désormait {1}".format(origin, dest, after.name, after.discriminator))

client.run(discordBotToken)