import praw
from discord.ext import commands
import discord
import requests # this is for the mtg search
from fuzzywuzzy import fuzz
import asyncio
import os # I need this to use environment variables on heroku
import csv # this is to browse the core set

# Reddit variables
reddit = praw.Reddit(client_id = 'x4FICJQqO4D14g' , client_secret = 'i9kip94Qs6R4Kfy77XYzDuv0z8Q' , user_agent = 'Card fetcher for Collective.') # gives access to reddit
collective = reddit.subreddit('collectivecg') # gives access to the Collective subreddit

# discord variables
bot = commands.Bot(command_prefix='!')
embed = discord.Embed(title = "CollectiveCardFetcher Help", description = "here is a list of commands for the bot:" , color= 0x00FFFF)
embed.add_field(name = '!alive', value = 'The bot will respond with "im alive and well!"')
embed.add_field(name = '!server', value = "The bot will respond with a link that can be used to add him to a server. note: you need to be an admin in a server to add a bot.")
embed.add_field(name = '!github', value = "The bot will respond with a link to the github page of the bot.")
embed.add_field(name = '!nice' , value = 'The bot will respond with a "nice art!" picture.')
embed.add_field(name = '!good' , value = 'Ups the score of the bot. Will make the bot respond with a thankful message.')
embed.add_field(name = '!bad', value = 'Reduces the score of the bot. Will make the bot respond with an apologetic message.')
embed.add_field(name = '!score' , value = 'the bot will respond with the amount of votes given to him trough !bad and !good')
embed.add_field(name = '!new', value = 'needs to be used with one of the following topics after: incubation, turns, keywords or collection. will return an explanation about said topic')
bot.remove_command('help')

# functions
def get_card_name(text):
    '''takes a string and extracts card names from it. card names are encapsulated in [[xxxx]] where xxxx is the card name'''
    cards = [] # list of names of cards
    start = text.find('[[')
    while start != -1: # until there are no more brackets
        end = text.find(']]')
        if end == -1:
            return cards # if there is an opener but no closer then someone fucked up
        else:
            query = text[start + 2:end]
            if query.find(':') > 0:
                mod = query[:query.find(':')].lower()
                card = query[query.find(':')+1:]
                if mod not in ['hs','eternal','mtg','core','reddit','dc','ygo','sb']:
                    card = query
                    mod = 'none'
                cards.append((mod,card))
            else:
                cards.append(('none',query)) # gets the name of the card
        text = text[end+2 : ] # cuts out the part with the card
        start = text.find('[[') # and the circle begins anew
    return cards

def save_card(name , link):
    '''saves a link to a card picture with the name specified in the temp_cards.csv document'''
    with open('temp_cards.csv' , 'a') as temp_cards_file:
        temp_cards = csv.writer(temp_cards_file , delimiter = ',')
        temp_cards.writerow([name , link])

def load_core_set():
    '''loads the core set cards from core_set.csv into a dictionary called core_set'''
    core_set = {}
    with open('core_set.csv' , 'r') as core_set_file:
        core_set_csv = csv.reader(core_set_file , delimiter = ',')
        for row in core_set_csv:
            name , link = row # unpack the row into a name and a link
            core_set[name] = link # adds the card into the core_set dictionary
    return core_set

def load_temp_cards():
    '''loads the temp saved cards from temp_cards.csv into a dictionary called temp_cards'''
    temp_cards = {}
    with open('temp_cards.csv' , 'r') as temp_cards_file:
        temp_cards_csv = csv.reader(temp_cards_file , delimiter = ',')
        for row in temp_cards_csv:
            if row != []: # there is a bug that adds empty lines .this prevent the program from crashing from it
                name , link = row # unpack the row into a name and a link
                temp_cards[name] = link # adds the card into the core_set dictionary
    return temp_cards

def get_card():
    '''fetches the newest card from reddit'''
    for card in collective.new(limit = 1):
        return 'https://www.reddit.com' + card.permalink

async def repost_card(post_channel):
    last_card = get_card()
    while True:
        card = get_card()
        if card != last_card:
            last_card = card
            await bot.send_message(post_channel , card)
        await asyncio.sleep(10)

def get_link(card):
    max_ratio = (' ', 0)  # maximum score in ratio exam
    max_partial = (' ', 0)  # maximum sort in partial ratio exam
    list_ratio = []
    list_partial = []
    #lets put the core_set and temp_cards together
    search_list = temp_cards.copy()
    search_list.update(core_set)
    for entry in search_list:
        # lets check if an entry is "good enough" to be our card
        ratio = fuzz.ratio(card, entry)
        partial = fuzz.partial_ratio(card, entry)
        if ratio > max_ratio[1]:
            max_ratio = (entry, ratio)
            list_ratio = [max_ratio]
        elif ratio == max_ratio[1]:
            list_ratio.append((entry, ratio))
        if partial > max_partial[1]:
            max_partial = (entry, partial)
            list_partial = [max_partial]
        elif partial == max_partial[1]:
            list_partial.append((entry, partial))
    if max_partial[1] > max_ratio[1]:
        return search_list[max_partial[0]]
    return search_list[max_ratio[0]]

def get_mtg(card):
    '''sends an image file of the mtg card'''
    # check scryfall api at scryfall website
    available = requests.get('https://api.scryfall.com/cards/named/', {'fuzzy': card}).json()
    if available['object'] == 'card':
        return 'https://api.scryfall.com/cards/named?fuzzy={};format=image;version=png'.format(card.replace(' ', '%20'))
    return "sorry, couldn't find {}. please try again.".format(card)

def get_top(num , week):
    return_list = []
    index = 1
    while index <= num:
        post = list(collective.search('flair:(week ' + str(week) + ')',limit = index , sort = 'top'))[-1]
        if post.title.startswith('[Card') or post.title.startswith('[Update'):
            return_list.append(post.url)
            index+=1
        else:
            num+=1
            index+=1
    return return_list

# commands
@bot.command()
async def alive():
    await bot.say('im alive and well!')

@bot.command()
async def server():
    await bot.say('https://discordapp.com/api/oauth2/authorize?client_id=465866501715525633&permissions=522304&scope=bot')

@bot.command()
async def github():
    await bot.say('https://github.com/fireasembler/CollectiveCardFetcher')

@bot.command(pass_context=True)
async def nice(ctx):
    await bot.send_file(ctx.message.channel, 'nice art.jpg')

@bot.command()
async def good():
    os.environ['GOOD'] = str(int(os.environ['GOOD']) + 1)
    await bot.say('thank you! :)')

@bot.command()
async def bad():
    os.environ['BAD'] = str(int(os.environ['BAD']) + 1)
    await bot.say('ill try better next time :(')

@bot.command()
async def score():
    await bot.say('good: ' + os.environ.get('GOOD'))
    await bot.say('bad: ' + os.environ.get('BAD'))

@bot.command()
async def new(link):
    if link == 'incubation':
        await bot.say("Hey! Welcome to the Collective discord server! We are in incubation mode right now, which means that no new alpha keys are being given out while the devs are working on new features for the game. You can still submit cards by proxy via the Editor Workshop channels (Art_Sharing for art, Card_Lab for design, Editor_Help for programming), many of our members would be happy to help you out there. Keep an eye out for opportunities for keys, as we occasionally host competitions that allow new players to receive a key if they join.\n\nSince many of our newcomers used to be disinclined to speak up, some of our members have put themselves forth as an offering to encourage activity. FireofGods will change his identity to the CardFetcherSpam bot for 24 hours for every new user who speaks up, while Feathers will change his name to any avian of your choice (real or fictional) for the same duration. Also, we have cake.\n\nIf you have any other question about the game, just ask. Have a great time here!")
    elif link == 'collection':
        await bot.say("https://www.collective.gg/collection")
    elif link == 'keywords':
        await bot.say('https://www.collective.gg/howtoplay2')
    elif link == 'turns':
        await bot.say("Each turn has two phases, the playing card/abilities phase, then the attack/block phase\nDuring the first phase, a player is assigned initiative, which alternates between players each turn\nPlayers simultaneously play their cards and activate unit abilities (actives). Their decisions don't happen immediately, but go on a stack where they wait to be resolved, until both players finished making their choices. Then, starting with the player with initiative, all cards/abilities are resolved in the order they were selected in.\nAfter all of the effects of the cards/abilities of the initiative player resolves, then all of the non-initiative player's actions resolve. That ends the first phase.\nDuring the second phase, players again make simultaneous decisions that don't take effect until both have confirmed their choices. Attackers are selected first. After those choices are locked in, then defenders are selected. After defenders are locked in, combat happens normally. The attack value of a unit is dealt cumulatively to each defender, not the same amount to each. As in - if you block an attacker with 1 attack and 2 health with two 1/1s, only one of them will die. The order in which you select blocks is the order in which units block. This can lead to situations where you block the 1/2 with a 0/3 and a 1/1 deadly, and the deadly unit will kill the 1/2 without taking damage, because you selected it to block second")

@bot.command(pass_context=True)
async def say(ctx):
    if ctx.message.author.id == '223876086994436097':
        await bot.delete_message(ctx.message)
        await bot.say(' '.join(ctx.message.content.split(' ')[1:]))
@bot.command()
async def help():
    await bot.say(embed=embed)

# events
@bot.event
async def on_message(message):
    cards = get_card_name(message.content) # this gets all card names in the message
    links = [] # here are the card links stored
    for card in cards:
        mod , card = card
        if card.lower().startswith('top '):
            if len(card.split(' ')) == 2: # the name looks like this :"top X"
                num = card.split(' ')[1]
                if num.isdigit():
                    links += get_top(int(num) , os.environ.get('WEEK'))
            elif len(card.split(' ')) == 4 and card.split(' ')[2] == 'week': # the name looks like this: "top X week Y"
                num = card.split(' ')[1]
                week = card.split(' ')[3]
                if num.isdigit() and week.isdigit():
                    links += get_top(int(num) , int(week))
        else:
            if mod == 'none' or mod == 'core':
                found = False
                if mod == 'none':
                    for post in collective.search(card , limit = 1): # this searches the subreddit for the card name with the [card] tag and takes the top suggestion
                        if post.title.startswith('['):
                            links.append(post.url)
                            found = True
                if not found: # if we didn't find any cards that go by that name
                    links.append(get_link(card))
            elif mod == 'mtg':
                links.append(get_mtg(card))
    if links: # if there are any links
        for x in range((len(links)//5)+1): # this loops runs one time plus once for every five links since discord can only display five pictures per message
            await bot.send_message(message.channel , '\n'.join(links[5*x:5*(x+1)]))
    await bot.process_commands(message)

#main
core_set = load_core_set()
temp_cards = load_temp_cards()
bot.run(os.environ.get('BOT_TOKEN'))