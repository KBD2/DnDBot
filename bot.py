import logging
import time
import random
import math
import discord
import string
import json
from urllib import request
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(20)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

botStart = time.time()
print("Bot started at {}.".format(time.asctime(time.localtime(time.time()))))

TOKEN = open('TOKEN', 'r').read()
VERSION = '1.0.1'

description = '''D&D Bot - Info and utilities for D&D version {}'''.format(VERSION)
bot = commands.Bot(command_prefix='~', description=description)

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='~help for commands'))
    print('Logged in.')

class DnD_Utility:
    """Useful D&D commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, mult=1, die='d20', add=0, adv='n'):
        """Rolls a D&D dice (Number of dice, die type, addon, advantage)"""
        self.dice = [4,6,8,10,12,20]
        self.rolls = []
        self.runs = 1
        self.total = 0
        adv = adv.lower()
        if  mult < 1 or mult > 1000:
            await self.bot.say("Multiplier cannot be lower than 1 or higher than 1000!")
            return 0
        if add < -1000 or add > 1000:
            await self.bot.say("Addition cannot be lower than -1000 or higher than 1000!")
            return 0
        if die[0].lower() == 'd': die = die[1:]
        try:
            die = int(die)
        except:
            await self.bot.say("Invalid die!")
            return 0
        if not die in self.dice:
            await self.bot.say("{} is not a valid D&D die!".format(die))
            return 0
        if adv == 'a' or adv == 'd': self.runs = 2
        for run in range(self.runs):
            self.subtotal = 0
            for roll in range(mult):
                self.subtotal += random.randint(1, die)
            self.rolls.append(self.subtotal + add)
        self.rolls.sort()
        if adv == 'a': self.total = self.rolls[1]
        else: self.total = self.rolls[0]
        await self.bot.say("You rolled {}".format(self.total))

bot.add_cog(DnD_Utility(bot))
    
class DnD_API:
    """Retrieve info on aspects of the 5th edition of DnD"""

    def __init__(self, bot):
        self.bot = bot
        self.allowed = string.ascii_letters + '_-'
        self.infobanks = [
            'races',
            'proficiencies',
            'spells',
            'monsters',
            'equipment',
            'skills',
            'classes',
            'subclasses'
            ]
        self.forbiddenkeys = [
            '_id',
            'url',
            'index',
            'ability_bonuses',
            'page'
            ]
        self.races = self.getData('http://www.dnd5eapi.co/api/races')
        self.proficiencies = self.getData('http://www.dnd5eapi.co/api/proficiencies')
        self.spells = self.getData('http://www.dnd5eapi.co/api/spells')
        self.monsters = self.getData('http://www.dnd5eapi.co/api/monsters')
        self.equipment = self.getData('http://www.dnd5eapi.co/api/equipment')
        self.skills = self.getData('http://www.dnd5eapi.co/api/skills')
        self.classes = self.getData('http://www.dnd5eapi.co/api/classes')
        self.subclasses = self.getData('http://www.dnd5eapi.co/api/subclasses')
        
    def getData(self, url):
        self.loaded = {}
        self.raw = request.urlopen(url).read().decode('utf-8')
        self.load = json.loads(self.raw)
        for item in self.load["results"]:
            self.name = item["name"].lower()
            self.name = self.name.replace(' ', '_')
            self.letter = 0
            while self.letter < len(self.name) - 1:
                if not self.name[self.letter] in self.allowed:
                    self.name = self.name[:self.letter] + self.name[self.letter + 1:]
                else: self.letter += 1
            self.loaded[self.name] = item["url"]
        return self.loaded

    async def concFromDictList(self, name, inp=[], onlyNames=False):
        self.ret = '{}: '.format(name.capitalize().replace('_', ' '))
        for idx in inp:
            if onlyNames: self.ret += str(idx['name']) + ', '
            else:
                if 'name' in list(idx.keys()):
                    self.ret += '\n' + self.concAllFromDict(idx['name'], idx) + ', '
                else:
                    self.ret += '\n' + self.concAllFromDict(name, idx) + ', '
            if len(self.ret) > 1000:
                await self.bot.say(self.ret)
                self.ret = ''
        return self.ret

    def concAllFromDict(self, name, inp=[]):
        self.ret = name.upper().replace('_', ' ') + '\n'
        for idx in list(inp.keys()):
            if idx in self.forbiddenkeys: continue
            self.ret += idx.capitalize().replace('_', ' ') + ': '
            if type(inp[idx]) == dict:
                if 'name' in list(inp[idx].keys()): self.ret += inp[idx]['name']
            elif idx == 'from':
                self.ret += ', '.join(str(i['name']) for i in inp[idx])
            else:
                self.ret += str(inp[idx])
            self.ret += '\n'
        self.ret += '-'
        return self.ret

    async def outputData(self, inp={}):
        await self.bot.say(inp['name'].capitalize().replace('_', ' '))
        for item in list(inp.keys()):
            if item in self.forbiddenkeys: continue
            self.inptype = type(inp[item])
            if self.inptype == str or self.inptype == int or self.inptype == float:
                await self.bot.say(item.capitalize().replace('_', ' ') + ': ' + str(inp[item]))
            elif self.inptype == dict:
                self.ret = self.concAllFromDict(item, inp[item])
                await self.bot.say(self.ret)
            elif self.inptype == list and len(inp[item]) > 0:
                if type(inp[item][0]) == dict:
                    self.ret = await self.concFromDictList(item, inp[item],
                                                      bool('url' in list(inp[item][0].keys()))
                                                      )
                    if len(self.ret) > 0: await self.bot.say(self.ret)
                else:
                    await self.bot.say(item.upper().replace('_', ' '))
                    for idx in inp[item]:
                        await self.bot.say(idx)
                    await self.bot.say('-')
            else:
                await self.bot.say(item.capitalize().replace('_', ' ') + ': '
                                   + str(inp[item]) * int(len(inp[item]) > 0))
            time.sleep(1)
    @commands.command()
    async def show(self, category='none'):
        """Lists all the items in a given category e.g. ~show classes"""
        category = category.lower()
        if category == 'none':
            await self.bot.say("This command needs a category!")
            return 0
        if not category in self.infobanks:
            await self.bot.say("That category doesn't exist in my directory!")
            return 0
        self.categoryInfo = self.getData('http://www.dnd5eapi.co/api/{}'.format(category))
        self.infoList = list(self.categoryInfo.keys())
        self.infoList.sort()
        self.count = 0
        self.idx = 0
        self.group = []
        while self.count < len(self.infoList):
            if self.infoList[self.count][0] == string.ascii_lowercase[self.idx]:
                self.group.append(self.infoList[self.count])
                self.count += 1
            else:
                if self.group != []: await bot.say(string.ascii_uppercase[self.idx] + ': '
                              + ', '.join(str(i) for i in self.group))
                self.group = []
                self.idx += 1
                time.sleep(1)
    
    @commands.command()
    async def getrace(self, race='none'):
        """Gets info on a given main race e.g. ~getrace dwarf"""
        race = race.lower()
        if race == 'none':
            await self.bot.say("This command needs a race!")
            return 0
        if not race in list(self.races.keys()):
            await self.bot.say("That race doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.races[race]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)

    @commands.command()
    async def getproficiency(self, proficiency='none'):
        """Gets info on a given proficiency e.g. ~getproficiency all_armor """
        proficiency = proficiency.lower()
        if proficiency == 'none':
            await self.bot.say("This command needs a proficiency!")
            return 0
        if not proficiency in list(self.proficiencies.keys()):
            await self.bot.say("That proficiency doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.proficiencies[proficiency]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)
        
    @commands.command()
    async def getspell(self, spell='none'):
        """Gets info on a given spell e.g. ~getspell fireball"""
        spell = spell.lower()
        if spell == 'none':
            await self.bot.say("This command needs a spell!")
            return 0
        if not spell in list(self.spells.keys()):
            await self.bot.say("That spell doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.spells[spell]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)
        
    @commands.command()
    async def getmonster(self, monster='none'):
        """Gets info on a given monster e.g. ~getmonster owlbear"""
        monster = monster.lower()
        if monster == 'none':
            await self.bot.say("This command needs a monster!")
            return 0
        if not monster in list(self.monsters.keys()):
            await self.bot.say("That monster doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.monsters[monster]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)

    @commands.command()
    async def getequipment(self, equipmentPiece='none'):
        """Gets info on a given piece of equipment e.g. ~getequipment dagger"""
        equipmentPiece = equipmentPiece.lower()
        if equipmentPiece == 'none':
            await self.bot.say("This command needs a piece of equipment!")
            return 0
        if not equipmentPiece in list(self.equipment.keys()):
            await self.bot.say("That piece of equipment doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.equipment[equipmentPiece]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)

    @commands.command()
    async def getskill(self, skill='none'):
        """Gets info on a given skill e.g. ~getskill acrobatics"""
        skill = skill.lower()
        if skill == 'none':
            await self.bot.say("This command needs a skill!")
            return 0
        if not skill in list(self.skills.keys()):
            await self.bot.say("That skill doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.skills[skill]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)

    @commands.command()
    async def getclass(self, classin='none'):
        """Gets info on a given class e.g. ~getclass fighter"""
        classin = classin.lower()
        if classin == 'none':
            await self.bot.say("This command needs a class!")
            return 0
        if not classin in list(self.classes.keys()):
            await self.bot.say("That class doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.classes[classin]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)

    @commands.command()
    async def getsubclass(self, subclass='none'):
        """Gets info on a given subclass e.g. ~getsubclass champion"""
        subclass = subclass.lower()
        if subclass == 'none':
            await self.bot.say("This command needs a subclass!")
            return 0
        if not subclass in list(self.subclasses.keys()):
            await self.bot.say("That subclass doesn't exist in my directory!")
            return 0
        self.raw = request.urlopen(self.subclasses[subclass]).read().decode('utf-8')
        self.data = json.loads(self.raw)
        await self.outputData(self.data)
        
bot.add_cog(DnD_API(bot))
    
class Utility:
    """Useful Stuff"""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def info(self):
        """Shows the bot's info"""
        self.uptimeCalc = time.time() - botStart
        self.days = math.floor(self.uptimeCalc / 86400)
        self.uptimeCalc -= self.days * 86400
        self.hours = math.floor(self.uptimeCalc / 3600)
        self.uptimeCalc -= self.hours * 3600
        self.minutes = math.floor(self.uptimeCalc / 60)
        await self.bot.say("```Uptime: {} days, {} hours, {} minutes\nVersion: {}```".format(
            self.days, self.hours, self.minutes, VERSION
            ))

    @commands.command()
    async def ping(self):
        """Pings the bot"""
        await self.bot.say("```Pong!```")
        
bot.add_cog(Utility(bot))

bot.run(TOKEN)
