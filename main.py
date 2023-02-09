import discord
import aiofiles
import aiohttp
import os
import re
import json
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import time
import aiosqlite
import random
import math
from PIL import Image, ImageOps, ImageDraw, ImageFont
import io
import textwrap
import itertools
import openai
from dotenv import load_dotenv
load_dotenv()

OPENAITOKEN = os.environ.get("OPENAITOKEN")
TOKEN = os.environ.get("TOKEN")
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='..', intents=intents)

#client.remove_command("help")

@client.event
async def on_ready():
    print("HEISENBOT IS NOW ONLINE.")
    
@client.event
async def on_guild_join(guild):
    async with aiosqlite.connect("./database.db") as db:
        await db.execute(f"CREATE TABLE '{guild.id}_words' (msg TEXT, is_img INTEGER, author_id INTEGER, channel_id INTEGER, id INTEGER)")
        await db.execute(f"CREATE TABLE '{guild.id}_markov' (id_or_general TEXT, word TEXT, pairs TEXT)")
        await db.commit()
        try:
            os.mkdir(f"./media/{guild.id}")
        except:
            pass
        await scan(guild) 
        print(f"CREATING TABLES FOR {guild.name} BY {guild.owner.name}#{guild.owner.discriminator}")
        print(f"DONE :)")
        
@client.event
async def on_guild_remove(guild):
    async with aiosqlite.connect("./database.db") as db:
        await db.execute(f"DROP TABLE '{guild.id}_words'")
        await db.execute(f"DROP TABLE '{guild.id}_markov'")
        await db.commit()
        print(f"DELETING TABLES FOR {guild.name} BY {guild.owner.name}#{guild.owner.discriminator}")

@client.command()
async def ping(ctx):
     await ctx.send(f'Pong! {round(client.latency * 1000)} ms')
        
async def scan(guild):
    async with aiosqlite.connect('./database.db') as db:
        #print("Starting scan...")
        for channel in guild.channels:
            if channel.type == discord.ChannelType.text:
                if channel.is_nsfw():
                    continue
                a = 0
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                async for message in channel.history():
                    if message.attachments != []: 
                        for a in message.attachments:
                            try:
                                await download(a,guild)
                                print(f"DOWNLOADING MEDIA \"{a.filename}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                            except:
                                continue
                    if message.content == "":
                        continue
                    elif message.content.endswith(".png") or message.content.endswith(".jpg") or message.content.endswith(".jpeg"):
                        try:
                            await download(message.content,guild,is_url=True)
                            print(f"DOWNLOADING URL-MEDIA \"{message.content}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                        except:
                            continue
                    await add_to_wordsdb(message, db)
                    pairs = await generate_pairs(message)
                    await add_to_markovdb(guild, pairs, db, message.author)
                    print(f"GENERATED MARKOV CHAIN AND ADDED \"{message.content}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                    

async def update_guilds(ctx):
    for guild in client.guilds:
        print("NEW GUILD FOUND :)")
        async with aiosqlite.connect("./database.db") as db:
            await db.execute(f"CREATE TABLE '{guild.id}_words' (msg TEXT, is_img INTEGER, author_id INTEGER, channel_id INTEGER, id INTEGER)")
            await db.execute(f"CREATE TABLE '{guild.id}_markov' (id_or_general TEXT, word TEXT, pairs TEXT)")
            await db.commit()
            try:
                await scan(guild)
            except:
                raise
            try:
                os.mkdir(f"./media/{guild.id}")
            except:
                continue
            print(f"CREATING TABLES FOR {guild.name} BY {guild.owner.name}#{guild.owner.discriminator}")
    print("DONE :))))")
#@client.command()
async def help(ctx, args=None):
    help_embed = discord.Embed(title="Heisenbot's commands")
    command_names_list = [x.name for x in client.commands]

    # If there are no arguments, just list the commands:
    if not args:
        help_embed.add_field(
            name="List of supported commands:",
            value="\n".join([str(i+1)+". "+x.name for i,x in enumerate(client.commands)]),
            inline=False
        )
        help_embed.add_field(
            name="Details",
            value="Type `..help <command name>` for more details about each command.",
            inline=False
        )

    # If the argument is a command, get the help text from that command:
    elif args in command_names_list:
        help_embed.add_field(
            name=args,
            value=client.get_command(args).help
        )

    # If someone is just trolling:
    else:
        help_embed.add_field(
            name="Nope.",
            value="Don't think I got that command, boss!"
        )

    await ctx.send(embed=help_embed)
@client.listen("on_message")
async def db_and_send(message):
    if message.content.startswith(".."):
        return
    async with aiosqlite.connect("./database.db") as db:
        if message.author != client.user:
            #SAVE MESSAGE TO DB
            if message.channel.is_nsfw():
                    return
            if message.attachments != []: 
                for a in message.attachments:
                    try:
                        await download(a,message.guild)
                        print(f"DOWNLOADING MEDIA \"{a.filename}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                    except:
                        continue
            if message.content == "":
                return
            for fname in message.content.split():
                if not any([fname.endswith(".mp4"),fname.endswith(".mp3"),fname.endswith(".jpeg"),fname.endswith(".jpg"),fname.endswith(".png"),fname.endswith(".wav"),fname.endswith(".gif"),fname.endswith(".mov"),fname.endswith(".avi"),fname.endswith(".pdf"),fname.endswith(".webm")]):
                    continue
                else:
                    try:
                        await download(fname,message.guild,is_url=True)
                        print(f"DOWNLOADING URL-MEDIA \"{fname}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                    except:
                        pass
            '''elif message.content.endswith(".png") or message.content.endswith(".jpg") or message.content.endswith(".jpeg") or message.content.endswith(".pdf") or message.content.endswith(".mp4") or message.content.endswith(".mp3") or message.content.endswith(".wav") or message.content.endswith(".gif") or message.content.endswith(".mov") or message.content.endswith(".avi") or message.content.endswith(".pdf") or message.content.endswith(".webm"):
                try:
                    await download(message.content,message.guild,is_url=True)
                    print(f"DOWNLOADING URL-MEDIA \"{message.content}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
                except:
                    pass'''
            if not message.content == "":
                await add_to_wordsdb(message, db)
                pairs = await generate_pairs(message)
                await add_to_markovdb(message.guild, pairs, db, message.author)
                print(f"GENERATED MARKOV CHAIN AND ADDED \"{message.content}\" FROM \"{message.channel.name}\" IN \"{message.guild.name}\".")
            #SEND MESSAGE
            will_of_god = random.randint(1,100)
            if will_of_god <= 35:
                gods_choice = random.randint(1,100)
                if gods_choice <= 80:
                    gods_word = await generate_text(db,message.guild)
                    print(f"SENDING \"{gods_word}\" TO \"{message.channel.name}\" IN \"{message.guild.name}\".")
                    await message.channel.send(gods_word)
                else:
                    x = random.choice(os.listdir(f"./media/{message.guild.id}/"))
                    file = f"./media/{message.guild.id}/" + x
                    gods_word = await generate_text(db,message.guild)
                    print(f"SENDING \"{gods_word}\" WITH FILE \"{x}\" TO \"{message.channel.name}\" IN \"{message.guild.name}\".")
                    await message.channel.send(gods_word, file=discord.File(file))
    #if "cum" in message.content:
    #    await message.add_reaction("😳")
        
@client.command(aliases=['gc'])
async def getcaptioned(ctx, member: discord.Member = None):
    if member is None:
        member = random.choice(ctx.guild.members)
    async with aiosqlite.connect("./database.db") as db:
        pfp = member.avatar_url_as(format="png")
        await pfp.save("./media/temp/pfp.png")
        #image = Image.open("./media/temp/pfp.png")
        #font = ImageFont.truetype("./fonts/impact.ttf",25)
        #image = image.resize((300,300))
        #draw = ImageDraw.Draw(image)
        text = username_to_string(await generate_text(db,ctx.guild))
        meme = Meme(text, "./media/temp/pfp.png")
        img = meme.draw()
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf,"PNG")
        pfp_send = io.BytesIO(buf.getvalue())
        print(f"SENDING PFP MEME USING \"{member.name}#{member.discriminator}\" WITH CAPTION \"{text}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
        await ctx.send(file=discord.File(pfp_send,filename="pfp.png"))

@client.command(aliases=["i"])
async def impact(ctx):
    async with aiosqlite.connect("./database.db") as db:
        text = username_to_string(await generate_text(db,ctx.guild))
        file = random.choice([x for x in os.listdir(f"./media/{ctx.guild.id}/") if x.endswith(".png") or x.endswith(".jpg") or x.endswith(".jpeg")])
        meme = Meme(text, f"./media/{ctx.guild.id}/{file}")
        img = meme.draw()
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf,"PNG")
        pfp_send = io.BytesIO(buf.getvalue())
        print(f"SENDING REGULAR MEME USING \"{file}\" WITH CAPTION \"{text}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
        await ctx.send(file=discord.File(pfp_send,filename="meme.png"))
@client.command()
async def invite(ctx):
    await ctx.message.reply("https://discord.com/api/oauth2/authorize?client_id=865060713347940382&permissions=517547220032&scope=bot")
@client.command(aliases=['ga'])
async def googleabuse(ctx, *, query):
    async with aiosqlite.connect("./database.db") as db:
        async with aiohttp.ClientSession() as session:
            text = username_to_string(await generate_text(db,ctx.guild))
            url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/ImageSearchAPI"
            number = None
            if query.split()[-1].isnumeric():
                number = int(query.split()[-1])
                query = ''.join(query[:-len(str(number))])
            querystring = {"q":query,"pageNumber":"1","pageSize":"50","autoCorrect":"false","safeSearch":"false"}
            headers = {
                'x-rapidapi-host': "contextualwebsearch-websearch-v1.p.rapidapi.com",
                'x-rapidapi-key': "178d7d6b59msha341fa94c1cbf06p164b47jsn2bc1febec334"
                }
            x = await (await session.get(url, headers=headers,params=querystring)).json()
            if number:
                info = x["value"][number]
            else:
                info = random.choice(x["value"])
            async with session.get(info["url"]) as resp:
                if not resp.status == 200:
                    await ctx.send(f"Error code {resp.status}. Maybe stop spamming it so much? Just a thought.")
                    return
                data = await resp.read()
            fname = "google.png"
            async with aiofiles.open(os.path.join(f"./media/temp/{fname}"), "wb") as outfile:
                await outfile.write(data)
            meme = Meme(text, f"./media/temp/{fname}")
            img = meme.draw()
            buf = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buf,"PNG")
            g_send = io.BytesIO(buf.getvalue())
            print(f"SENDING GOOGLE MEME USING WORD \"{query}\" WITH CAPTION \"{text}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
            await ctx.send(file=discord.File(g_send,filename="googlememe.png"))
            
@client.command(aliases=['g'])
async def generate(ctx, member: discord.Member = None):
    async with aiosqlite.connect("./database.db") as db:
        gods_choice = random.randint(1,100)
        if member is None:
            gods_word = await generate_text(db,ctx.guild)
        else:
            gods_word = await generate_user_text(db,ctx.guild,member)
        if gods_choice <= 80:
            print(f"SENDING \"{gods_word}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
            await ctx.send(gods_word)
        else:
            x = random.choice(os.listdir(f"./media/{ctx.guild.id}/"))
            file = f"./media/{ctx.guild.id}/" + x
            print(f"SENDING \"{gods_word}\" WITH FILE \"{x}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
            await ctx.send(gods_word, file=discord.File(file))
#@client.command(aliases=['gu'])
async def generate_user(ctx, member: discord.Member):
    async with aiosqlite.connect("./database.db") as db:
        gods_word = await generate_user_text(db,ctx.guild,member)
        print(f"SENDING \"{gods_word}\" BY \"{member.name}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
        await ctx.send(gods_word)

@client.command(aliases=['d'])
async def demotivator(ctx):
    async with aiosqlite.connect("./database.db") as db:
        filepath = f"./media/{ctx.guild.id}/" + random.choice([x for x in os.listdir(f"./media/{ctx.guild.id}/") if x.endswith(".png") or x.endswith(".jpg") or x.endswith(".jpeg")])
        motivation = username_to_string(await generate_text(db, ctx.guild,1))
        description = username_to_string(await generate_text(db,ctx.guild,7))
        msize = 85
        dsize =  40
        output = "./media/temp/motivate.png"
        motivate_image(filepath, motivation, msize, description, dsize, output)
        print(f"SENDING MOTIVATOR MEME USING \"{filepath}\" WITH WORD \"{motivation}\" WITH DESCRIPTION \"{description}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
        await ctx.send(file=discord.File(output))

@client.command(aliases=['gr'])
async def generaterandom(ctx):
    if not ctx.author.id == 125788547939696640:
        await ctx.send("this command isnt for you :(")
        return
    guild = client.get_guild(random.choice([int(x) for x in os.listdir("./media/") if not x == "temp"]))
    async with aiosqlite.connect("./database.db") as db:
        gods_choice = random.randint(1,100)
        try:
            gods_word = await generate_text(db,guild)
        except:
            await ctx.send("Oopsies!!!! I selected a server im not in anymore!!")
            return
        if gods_choice <= 80:
            print(f"SENDING \"{gods_word}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
            await ctx.send(gods_word)
        else:
            x = random.choice(os.listdir(f"./media/{guild.id}/"))
            file = f"./media/{guild.id}/" + x
            print(f"SENDING \"{gods_word}\" WITH FILE \"{x}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
            await ctx.send(gods_word, file=discord.File(file))
@client.command(aliases=['grm'])
async def generaterandommedia(ctx):
    if not ctx.author.id == 125788547939696640:
        await ctx.send("this command isnt for you :(")
        return
    listOfFiles = []
    directory = "./media/"
    for (dirpath, dirnames, filenames) in os.walk(directory):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]
    file = random.choice(listOfFiles)
    print(f"SENDING FILE \"{file}\" TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
    await ctx.send(file=discord.File(file))
@client.command(aliases=['r'])
async def rage(ctx):
    async with aiosqlite.connect("./database.db") as db:
        number = random.choice([1,4])
        panelimage = Image.open(f"./templates/comics/panels/2.png")
        panelW, panelH = panelimage.size
        font = "./fonts/NewBaskerville Regular.ttf"
        maxH = int((panelH - (panelH/8))-(panelH/4))
        finished = []
        for x in range(number):
            test = panelimage.copy()
            temp = username_to_string(await generate_text(db,ctx.guild)).encode('latin-1','ignore').decode(encoding='latin-1',errors='ignore')
            wrapper = textwrap.TextWrapper(width=50)
            temp = wrapper.wrap(text=temp)
            text = ""
            for word in temp:
                text += f"{word}\n"
            #await ctx.send(text)
            #print(text)
            face = Image.open(f"./templates/comics/faces/{random.choice(os.listdir('./templates/comics/faces/'))}")
            face = ImageOps.contain(face,(1000,150))
            w, h = face.size
            desiredW = int(panelW/2) - int((w/2))
            desiredH = int(panelH - (panelH/8)) - h
            
            test.paste(face,(desiredW,desiredH))
            draw = ImageDraw.Draw(test)
            w, h = draw.textsize(text)
            draw.text((panelW/2-int(w/2)-20,panelH/4-h),text,font=ImageFont.truetype(font,16),fill='black')
            finished.append(test)
        print(f"SENDING {number} PANEL RAGE COMIC TO \"{ctx.channel.name}\" IN \"{ctx.guild.name}\".")
        if len(finished) == 1:
            finished[0].save(r"./media/temp/rage.png")
            await ctx.send(file=discord.File("./media/temp/rage.png"))
            #os.remove("./media/temp/rage.png")
        elif len(finished) == 4:
            fourpanel = Image.new(mode="RGB",size=(panelW*2,panelH*2),color = (255,255,255))

            #paste the panels
            fourpanel.paste(finished[0],(0,0))
            fourpanel.paste(finished[1],(panelW,0))
            fourpanel.paste(finished[2],(0,panelH))
            fourpanel.paste(finished[3],(panelW,panelH))
            
            #draw panel dividers
            fourdraw = ImageDraw.Draw(fourpanel)
            coordshorizontal = ((0,panelH),(panelW*2,panelH))
            fourdraw.line(coordshorizontal,fill="black",width=2)
            coordsvertical = ((panelW,0),(panelW,panelH*2))
            fourdraw.line(coordsvertical,fill="black",width=2)
            
            fourpanel.save(r"./media/temp/rage.png")
            await ctx.send(file=discord.File("./media/temp/rage.png"))
            #os.remove("./media/temp/rage.png")
def username_to_string(sentence):
    temp = []
    for word in sentence.split():
        m = re.search("<@!?(\d*)>",word)
        if m:
            x = client.get_user(int(m.group(1)))
            print(x)
            if x:
                temp.append(f"@{x.name} ")
            else:
                temp.append(f"{word} ")
        else:
            temp.append(f"{word} ")
    return "".join(temp)
class Meme:

    basewidth = 1200            #Width to make the meme
    fontBase = 100              #Font size
    letSpacing = 9              #Space between letters
    fill = (255, 255, 255)      #TextColor
    stroke_fill = (0,0,0)       #Color of the text outline
    lineSpacing = 10            #Space between lines
    stroke_width=9              #How thick the outline of the text is
    fontfile = './fonts/impact.ttf'

    def __init__(self, caption, image):
        self.img = self.createImage(image)
        self.d = ImageDraw.Draw(self.img)

        self.splitCaption = textwrap.wrap(caption, width=20)  # The text can be wider than the img. If thats the case split the text into multiple lines
        self.splitCaption.reverse()                           # Draw the lines of text from the bottom up

        fontSize = self.fontBase+10 if len(self.splitCaption) <= 1 else self.fontBase   #If there is only one line, make the text a bit larger
        self.font = ImageFont.truetype(font=self.fontfile, size=fontSize)
        # self.shadowFont = ImageFont.truetype(font='./impact.ttf', size=fontSize+10)

    def draw(self):
        '''
        Draws text onto this objects img object
        :return: A pillow image object with text drawn onto the image
        '''
        (iw, ih) = self.img.size
        (_, th) = self.d.textsize(self.splitCaption[0], font=self.font) #Height of the text
        y = (ih - (ih / 10)) - (th / 2) #The starting y position to draw the last line of text. Text in drawn from the bottom line up

        for cap in self.splitCaption:   #For each line of text
            (tw, _) = self.d.textsize(cap, font=self.font)  # Getting the position of the text
            x = ((iw - tw) - (len(cap) * self.letSpacing))/2  # Center the text and account for the spacing between letters

            self.drawLine(x=x, y=y, caption=cap)
            y = y - th - self.lineSpacing  # Next block of text is higher up

        wpercent = ((self.basewidth/2) / float(self.img.size[0]))
        hsize = int((float(self.img.size[1]) * float(wpercent)))
        return self.img.resize((int(self.basewidth/2), hsize))

    def createImage(self, image):
        '''
        Resizes the image to a resonable standard size
        :param image: Path to an image file
        :return: A pil image object
        '''
        img = Image.open(image)
        wpercent = (self.basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        return img.resize((self.basewidth, hsize))

    def drawLine(self, x, y, caption):
        '''
        The text gets split into multiple lines if it is wider than the image. This function draws a single line
        :param x: The starting x coordinate of the text
        :param y: The starting y coordinate of the text
        :param caption: The text to write on the image
        :return: None
        '''
        for idx in range(0, len(caption)):  #For each letter in the line of text
            char = caption[idx]
            w, h = self.font.getsize(char)  #width and height of the letter
            self.d.text(
                (x, y),
                char,
                fill=self.fill,
                stroke_width=self.stroke_width,
                font=self.font,
                stroke_fill=self.stroke_fill
            )  # Drawing the text character by character. This way spacing can be added between letters
            x += w + self.letSpacing #The next character must be drawn at an x position more to the right


def text_wrap(text, font, max_width):
    """Wrap text base on specified width. 
    This is to enable text of width more than the image width to be display
    nicely.
    @params:
        text: str
            text to wrap
        font: obj
            font of the text
        max_width: int
            width to split the text with
    @return
        lines: list[str]
            list of sub-strings
    """
    lines = []
    
    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0]  <= max_width:
        lines.append(text)
    else:
        #split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i]+ " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return lines
async def generate_user_text(db,guild,member):
    cur = await db.execute(f"SELECT word, pairs FROM '{guild.id}_markov' WHERE id_or_general=? ORDER BY RANDOM() LIMIT 1",(member.id,))
    info = await cur.fetchone()
    startingword = info[0]
    phrase = startingword + " "
    pairs = info[1].split()
    banana = True
    while banana:
        chosen = random.choice(pairs)
        if chosen == "EOL":
            break
        phrase += chosen + " "
        #if random.randint(1,100) < 3:
            #banana = False
        cur = await db.execute(f"SELECT pairs FROM '{guild.id}_markov' WHERE id_or_general=? AND word=?",(member.id, chosen))
        pairs = (await cur.fetchone())[0].split()
    return phrase
async def generate_text(db,guild,limit=None):
    cur = await db.execute(f"SELECT word, pairs FROM '{guild.id}_markov' WHERE id_or_general='general' ORDER BY RANDOM() LIMIT 1")
    info = await cur.fetchone()
    startingword = info[0]
    phrase = startingword + " "
    pairs = info[1].split()
    banana = True
    while banana:
        if limit:
            if len(phrase.split()) >= limit:
                break
        chosen = random.choice(pairs)
        if chosen == "EOL":
            break
        phrase += chosen + " "
        #if random.randint(1,100) < 3:
            #banana = False
        cur = await db.execute(f"SELECT pairs FROM '{guild.id}_markov' WHERE id_or_general='general' AND word=?",(chosen,))
        pairs = (await cur.fetchone())[0].split()
    return phrase
def list_to_db(words):
    db_list = ""
    for word in words:
        db_list += str(word)+" "
    return db_list
    
async def add_to_markovdb(guild, pairs, db, user):
    for pair in pairs:
        gencur = await db.execute(f"SELECT pairs FROM '{guild.id}_markov' WHERE word=? AND id_or_general='general'", (pair[0],))
        gen = await gencur.fetchone()
        if not gen is None:
            personalcur = await db.execute(f"SELECT pairs FROM '{guild.id}_markov' WHERE word=? AND id_or_general='{user.id}'",(pair[0],))
            personal = await personalcur.fetchone()
            if personal is None:
                await db.execute(f"INSERT INTO '{guild.id}_markov' VALUES (?, ?, ?)", (user.id, pair[0], pair[1]))
                await db.commit()
                personalcur = await db.execute(f"SELECT pairs FROM '{guild.id}_markov' WHERE word=? AND id_or_general='{user.id}'",(pair[0],))
                personal = await personalcur.fetchone()
            personal_list = personal[0].split()
            gen_list = gen[0].split()
            personal_list.append(pair[1])
            gen_list.append(pair[1])
            await db.execute(f"UPDATE '{guild.id}_markov' SET pairs=? WHERE word=? AND id_or_general=?",(list_to_db(gen_list),pair[0],"general"))
            await db.execute(f"UPDATE '{guild.id}_markov' SET pairs=? WHERE word=? AND id_or_general=?",(list_to_db(personal_list),pair[0],user.id))
            await db.commit()
        else:
            await db.execute(f"INSERT INTO '{guild.id}_markov' VALUES (?, ?, ?)", ("general", pair[0], pair[1]))
            await db.execute(f"INSERT INTO '{guild.id}_markov' VALUES (?, ?, ?)", (user.id, pair[0], pair[1]))
            await db.commit()
            
async def add_to_wordsdb(message, db):
    msg = message.content
    if any([msg.endswith(".jpg"),msg.endswith(".png"),msg.endswith(".jpeg")]):
        is_img = 1
    else:
        is_img = 0
    author_id = message.author.id
    channel_id = message.channel.id
    id = message.id
    await db.execute(f"INSERT INTO '{message.guild.id}_words' VALUES (?, ?, ?, ?, ?)", (msg, is_img, author_id, channel_id, id))
    await db.commit()
    
async def generate_pairs(message):
    if not message.content == "":
        pairs = []
        words = message.content.split()
        for ind, word in enumerate(words):
            if ind == len(words)-1:
                pairs.append((word,'EOL'))
            else:
                pairs.append((word,words[ind+1]))
    return pairs
    
async def download(attachment, guild,is_url=False):
    if is_url:
        url = attachment
        fname = str(random.randint(1,100000)) + url.split("/")[-1]
    else:
        url = attachment.url
        fname = str(random.randint(1,100000)) + attachment.filename
    if not any([fname.endswith(".mp4"),fname.endswith(".mp3"),fname.endswith(".jpeg"),fname.endswith(".jpg"),fname.endswith(".png"),fname.endswith(".wav"),fname.endswith(".gif"),fname.endswith(".mov"),fname.endswith(".avi"),fname.endswith(".pdf"),fname.endswith(".webm")]):
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            assert resp.status == 200
            data = await resp.read()
    async with aiofiles.open(
        os.path.join(f"./media/{guild.id}", fname), "wb"
    ) as outfile:
        await outfile.write(data)
def motivate_image(image, motivation, motivation_size, description, description_size, output):
    border_size = 35
    text_padding = 15

    # Get the image from the args
    motivational_image = Image.open(image)
    size = 1200, 1200
    motivational_image.thumbnail(size,Image.ANTIALIAS)
    bordered_image = ImageOps.expand(motivational_image, border=border_size, fill=0)
    #font = './fonts/Glegoo-Regular.ttf'
    font = './fonts/NewBaskerville Regular.ttf'
    # Fun with fonts
    motivation_font = ImageFont.truetype(font, motivation_size)
    description_font = ImageFont.truetype(font, description_size)
    motivation_size = motivation_font.getsize(motivation)
    description_size = description_font.getsize(description)

    # Create an image large enough to hold the text and the motivational image
    background_image_width = bordered_image.size[0] # size[0] is the width of an Image
    background_image_height = motivation_size[1] + description_size[1] + \
            text_padding * 2 + bordered_image.size[1]
    background_image_size = (background_image_width, background_image_height)

    background_image = Image.new('RGB', background_image_size, 'black')

    # Figure out where to center our text
    motivation_left_buffer = (background_image_width / 2) - (motivation_size[0] / 2)
    description_left_buffer = (background_image_width / 2) - (description_size[0] / 2)

    description_bottom_buffer = background_image_height - text_padding - description_size[1]
    motivation_bottom_buffer = description_bottom_buffer - text_padding - motivation_size[1]

    # Print the text on the image
    dr = ImageDraw.Draw(background_image)

    dr.text((motivation_left_buffer, motivation_bottom_buffer),
            motivation,
            font=motivation_font,
            fill='#FFFFFF')

    dr.text((description_left_buffer, description_bottom_buffer),
            description,
            font=description_font,
            fill='#FFFFFF')

    # Paste our original image onto the background with text
    background_image.paste(bordered_image, (0, 0))

    # Save or show your image
    if output:
        try:
            background_image.save(output)
        except:
            print("Sorry, couldn't save your image. Check to make sure the output path is accessible")
            background_image.show()
    else:
        background_image.show()
    

openai.api_key = OPENAITOKEN
@client.command(aliases=["p"])
async def prompt(ctx,*,pro):
    response = openai.Completion.create(
  model="text-davinci-002",
  prompt=pro,
  temperature=0.8,
  max_tokens=500,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)
    await ctx.send(pro+response["choices"][0]["text"])   

    
client.run(TOKEN)
