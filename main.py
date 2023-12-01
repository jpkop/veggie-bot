import datetime
import sqlite3
import random
import requests
import json
import time


class Veggie(object):
    def __init__(self, name, factor, amount, category):
        self.name = name
        self.factor = factor
        self.amount = amount
        self.category = category

# Fetch data from sqlite database
def fetchData(month):
    connection = sqlite3.connect("db/vegetaries.sqlite")
    cursor = connection.cursor()

    cursor.execute("SELECT name, factor, amount, category FROM vegetaries WHERE " + month + " = 1 ORDER BY category")

    content = cursor.fetchall()
    connection.close()
    return content


def getCurrentMonth():
    date = datetime.datetime.now()
    month = date.strftime("%b").lower()
    return month


def getRandomNumber(interval):
    return int(random.random() * interval)

# create List with one random veg per category
# every veg which has season and has a factor higher than 1 (means it has only a short season) is put into
# category "special"
def createVegList(data):
    veggiesCollection = {}
    for args in data:
        veg = Veggie(*args)
        veggiesCollection[veg.name] = veg

    categoriesCollection = {}

    for veg in data:
        name = veg[0]
        factor = veg[1]
        amount = veg[2]
        category = veg[3]

        # if category already exists, order veggie in there
        if category in categoriesCollection:
            key = category
            value = categoriesCollection[key]
            value.append({"name": name, "factor": factor, "amount": amount})
        # if not create category
        else:
            key = category
            value = [{"name": name, "factor": factor, "amount": amount}]
        categoriesCollection[key] = value


    choice = {"special": []}
    for item in categoriesCollection:
        # print(item, "has", len(categoriesCollection[item]), "entries")

        for index, veg in enumerate(categoriesCollection[item]):
            # print("index", index, veg)

            if veg["factor"] > 1:
                # if entry not exists then add veg, else append it
                if len(choice["special"]) == 0:
                    choice["special"] = [veg]
                else:
                    choice["special"].append(veg)

        # if a category has more than one veg that is in season, randomly chose one of them for the choice list
        if len(categoriesCollection[item]) > 1:
            nummer = getRandomNumber(len(categoriesCollection[item]))
            # print(categoriesCollection[item][nummer])
            choice[item] = categoriesCollection[item][nummer]
        else:
            choice[item] = categoriesCollection[item][0]

    return choice

# create the message for the telegram bot
def createMessage(vegList):
    # Veggie Choice of the week
    messageToSend = ("*Die Gemüseauswahl der Woche*\n \n")
    for category in vegList:
        if category == "special":
            continue
        else:
            messageToSend = messageToSend + str(vegList[category]["amount"]) + " " + str(
                vegList[category]["name"]) + "\n"

    messageToSend = messageToSend + "\nKurzzeitig Saison haben: \n"

    for element in vegList["special"]:
        messageToSend = messageToSend + element["name"] + " \\(" + element["amount"] + "\\) \n"

    print(messageToSend)
    return messageToSend


def request(token):
    answer = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
    print(answer)
    content = answer.content
    data = json.loads(content)
    print(data)
    return data

# send message as the telegram veggie bot
def sendMessage(token, chatId, messageToSend):
    requestData = request(token)

    if (requestData["ok"]):
        print("send message")
        # die chat_id ist die aus der obigen Response
        params = {"chat_id": chatId, "parse_mode": "MarkdownV2", "text": messageToSend}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = requests.post(url, params=params)
        message



# get the telegram bot token and chatId from file
with open("token.txt") as file:
    fileInput = file.read()
split = fileInput.split('"')
token = split[3]
chatId = split[7]
print("Token: " + token + "chatId: " + chatId)


# fetch data from database which has season in the current month
data = fetchData(getCurrentMonth())
# create choice of veggies
vegList = createVegList(data)
# create message based on choice
messageToSend = createMessage(vegList)
#send the message as the telegram bot
sendMessage(token, chatId, messageToSend)