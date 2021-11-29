import os
import discord
import random
import json
import DiscordUtils
import pafy
import itertools 
from discord.ext import commands, tasks
from ballreplies import replies
from workreplies import wreplies
from random import choice
from os import system 
from music import Music
from itertools import cycle
from permissiondeniedreplies import preplies

intents = discord.Intents.default()
intents.members = True
client = commands.Bot('$', intents=intents, description='Yet another music bot.')
music = DiscordUtils.Music()
status = cycle(['Watching being worked on', 'Watching me causing the programmers pain'])

earningRange = 18


@client.event
async def on_ready():
    print(f"Init as {client.user}")
    change_status.start()

@tasks.loop(minutes=20)
async def change_status(): 
    await client.change_presence(activity=discord.Game(next(status)))

mainshop = [{"name":"YAGPDBCommand","price":1000,"description":"You get your own YAGPDB command! Contact one of the admins and send them the gif and/or some text with your gif! (Can be bought multiple times)"}]

@client.command(aliases=['8ball',]) #8ball WOOOOOOO!
async def _8ball(ctx, *, question):
    embed = discord.Embed()
    embed.color = discord.Color.purple()
    embed.title = "Magic 8 Ball"
    embed.description = f'Question: {question}\nAnswer: {random.choice(replies)}'
    await ctx.send(embed=embed)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.title = 'Error, Command not found!'
        embed.description = "Please check your command and try again."
        await ctx.send(embed=embed)

@client.command(aliases = ['purge'])
async def clear(ctx, amount : int): 
    authorperms = ctx.author.permissions_in(ctx.channel)
    if authorperms.manage_messages:
        await ctx.channel.purge(limit=amount)
    else:
        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.title = f'{random.choice(preplies)}'
        await ctx.send(embed=embed)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.title = 'Error!'
        embed.description = 'Please specify the number of messages to delete.'
        await ctx.send(embed=embed)


@client.command()
async def ping(ctx):
    embed = discord.Embed()
    embed.color = discord.Color.purple()
    embed.title = f'Pong! {round(client.latency * 1000)}ms'
    await ctx.send(embed=embed)


@client.command(name='credits', help='This command returns the credits')
async def credits(ctx):
    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Made by Hybrid...and pain'
    await ctx.send(embed=embed)


@client.command()
@commands.cooldown(1, 600, commands.BucketType.user)
async def work(ctx):
    await open_account(ctx.author)

    users = await get_bank_data()

    user = ctx.author

    earnings = random.randrange(200)

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.description = f"{random.choice(wreplies)}\nYou have recieved ¥{earnings}!"
    await ctx.send(embed=embed)

    users[str(user.id)]["wallet"] += earnings

    with open ("mainbank.json", "w") as f:
        json.dump(users,f)

@work.error
async def mine_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.title = 'GET SOME REST!'
        embed.description = 'This command is ratelimited, please try again in {:.0f}s'.format(error.retry_after)
        await ctx.send(embed=embed)
    else:
        raise error

#used to check your balance
@client.command(aliases = ['bal'])
async def balance(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"] 
    bank_amt = users[str(user.id)]["bank"] 

    em = discord.Embed(title = f"{ctx.author.name}'s balance",color = discord.Color.blurple())
    em.add_field(name = "Wallet balance", value = wallet_amt)
    em.add_field(name = "Bank balance", value = bank_amt)
    await ctx.send(embed = em)

#used to deposit money from your wallet into your account
@client.command(aliases = ['dep'])
async def deposit(ctx,amount = None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("`Transaction failed! Please specifiy amount that you want to deposit!`")
        return

    bal = await update_bank(ctx.author)
    if amount == "all":
        amount = bal[0]

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send("`Transaction failed! You do not have that much money in your wallet!`")
        return
    if amount<0:
        await ctx.send("`Transaction failed! Please input a positive number!`")
        return

    await update_bank(ctx.author,-1*amount)
    await update_bank(ctx.author,amount, "bank")

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Transaction successful!'
    embed.description = f'You have successfully deposited ¥{amount} into your account!'
    await ctx.send(embed=embed)


@client.command()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def rob(ctx,member:discord.Member,amount = None):
    await open_account(ctx.author)
    await open_account(member)

    bal = await update_bank(member)

    amount = int(amount)
    if bal[0]<100:
        await ctx.send("`It's not worth it mate.`")
        return

    earnings = random.randrange(0, bal[0])

    await update_bank(ctx.author,earnings)
    await update_bank(member,-1*earnings)

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Petty Theft!'
    embed.description = f'You have successfully robbed someone for ¥{amount}!'
    await ctx.send(embed=embed)

@rob.error
async def mine_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.title = 'You have already robbed today!'
        embed.description = 'This command is ratelimited, please try again in {:.0f}s'.format(error.retry_after)
        await ctx.send(embed=embed)
    else:
        raise error

#used to send a user money from your account
@client.command()
async def send(ctx,member:discord.Member,amount = None):
    await open_account(ctx.author)
    await open_account(member)

    if amount == None:
        await ctx.send("`Transaction failed! Please specifiy amount that you want to send!`")
        return

    bal = await update_bank(ctx.author)
    if amount == "all":
        amount = bal[0]

    amount = int(amount)
    if amount>bal[1]:
        await ctx.send("`Transaction failed! You do not have enough money in your account!`")
        return
    if amount<0:
        await ctx.send("`Transaction failed! Please input a positive number!`")
        return


    await update_bank(ctx.author,-1*amount, "bank")
    await update_bank(member,amount, "bank")

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Transaction successful!'
    embed.description = f'You have successfully wired ¥{amount} into their account!'
    await ctx.send(embed=embed)

#used to take money out of your account and put into your wallet
@client.command(aliases = ['with'])
async def withdraw(ctx,amount = None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("`Transaction failed! Please specifiy amount that you want to withdraw!`")
        return

    bal = await update_bank(ctx.author)
    if amount == "all":
        amount = bal[0]


    amount = int(amount)
    if amount>bal[1]:
        await ctx.send("`Transaction failed! You do not have enough money in your account!`")
        return
    if amount<0:
        await ctx.send("`Transaction failed! Please input a positive number!`")
        return

    await update_bank(ctx.author,amount)
    await update_bank(ctx.author,-1*amount, "bank")

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Transaction successful!'
    embed.description = f'You have successfully withdrawn ¥{amount} from your account!'
    await ctx.send(embed=embed)


@client.command()
async def shop(ctx):
    em = discord.Embed(
        title = "Shop", 
        color = discord.Color.orange()
        )

    for item in mainshop:
        name = item["name"]
        price = item["price"]
        desc = item["description"]
        em.add_field(name = name, value = f"¥{price} \n {desc}")

    await ctx.send (embed = em)


@client.command()
async def buy(ctx, item, amount = 1):
    await open_account(ctx.author)  # if already has account, do nothing. If not, open one

    res = await buy_this(ctx.author, item, amount)


    if not res[0]:          # 0 is returned to the "res" as the default
        if res[1] == 1:     # this happens when error code 1 happens
            await ctx.send("`You didn't state the item!`")
            return
        if res[1] == 2:     # this is returned when user doesn't have enough money
            await ctx.send("`You don't have enough money!`")
            return

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Transaction successful!'
    embed.description = f'You have successfully bought {amount} {item}(s)!'
    await ctx.send(embed=embed)


@client.command()
async def bag(ctx):
    await open_account(ctx.author)    # making sure author has account
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]
    except:
        bag = []            # bag is an empty list of the things the user has

    embed = discord.Embed(
        title = "Bag", color = discord.Color.blurple())        # just an embed to show what's in the bag
    for item in bag:
        name = item["item"]
        amount = item["amount"]


        embed.add_field(name = name, value = amount)
    await ctx.send(embed = embed)


async def buy_this(user,item_name,amount):
    item_name = item_name.upper()
    name_ = None
    for item in mainshop:
        name = item["name"].upper()()
        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0]<cost:
        return [False,2]


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt + amount
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            obj = {"item":item_name , "amount" : amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item":item_name , "amount" : amount}
        users[str(user.id)]["bag"] = [obj]        

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost*-1,"wallet")

    return [True,"Worked"]


@client.command()
async def sell(ctx,item,amount):
    await open_account(ctx.author)

    res = await sell_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That Object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have {amount} {item} in your bag.")
            return
        if res[1]==3:
            await ctx.send(f"You don't have {item} in your bag.")
            return

    embed = discord.Embed()
    embed.color = discord.Color.green()
    embed.title = 'Transaction successful!'
    embed.description = f'You have successfully sold {amount} {item}(s)!'
    await ctx.send(embed=embed)

async def sell_this(user,item_name,amount,price = None):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            if price==None:
                price = 0.9* item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt - amount
                if new_amt < 0:
                    return [False,2]
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            return [False,3]
    except:
        return [False,3]    

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost,"wallet")

    return [True,"Worked"]
                
@client.command(aliases = ["lb" , "LB" , "Lb"])
async def leaderboard(ctx,x = 10):
    users = await get_bank_data()
    leader_board = {}
    total = []
    for user in users:
        name = int(user)
        total_amount = users[user]["wallet"] + users[user]["bank"]
        leader_board[total_amount] = name
        total.append(total_amount)

    total = sorted(total,reverse=True)    

    em = discord.Embed(title = f"Top {x} Richest People", 
    description = "This is decided on the basis of net worth",
    color = discord.Color(0xfa43ee))
    index = 1
    for amt in total:
        id_ = leader_board[amt]
        member = bot.get_user(id_)
        name = member.name
        em.add_field(name = f"{index}. {name}" , value = f"```CSS\n[¥{amt}]```",  inline = False)
        if index == x:
            break
        else:
            index += 1

    await ctx.send(embed = em)

async def open_account(user):

    users = await get_bank_data()

    with open("mainbank.json", "r") as f:
        users = json.load(f)

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0
        users[str(user.id)]["bank"] = 0

    with open ("mainbank.json", "w") as f:
        json.dump(users,f)
    return True

async def get_bank_data():
    with open("mainbank.json", "r") as f:
        users = json.load(f)
    return users 

async def update_bank(user,change = 0, mode = "wallet"):
    users = await get_bank_data()

    users[str(user.id)][mode] += change

    with open ("mainbank.json", "w") as f:
        json.dump(users,f)
    
    bal = [users[str(user.id)]["wallet"],users[str(user.id)]["bank"]]
    return bal

async def setup():
    await client.wait_until_ready()
    client.add_cog(Music(client))


client.loop.create_task(setup())
client.run("")