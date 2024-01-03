# main.py

# IMPORT OS MODULE
import os
# IMPORT DISCORD.PY - ALLOWS ACCESS TO DISCORD'S API
import discord
from discord import Colour
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
# IMPORT FOR ENV READING
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True
intents.messages = True
# bot - DISCORD CLIENT INSTANCE
bot = discord.Client(intents=intents)

# tree - HOLDS ALL APPLICATION COMMANDS
tree = discord.app_commands.CommandTree(bot)

# EVENT LISTENER FOR WHEN BOT TURNS ONLINE
@bot.event
async def on_ready():
    await tree.sync()
    print("-----------------------------------------------")

class EmbedData:
    def __init__(self, title, description, color, traces, relics, planetary
                 , mainstats, substats, lightcones
                 ):
        self.title = title
        self.description = description
        self.color = color
        self.traces = traces
        self.relics = relics
        self.planetary = planetary
        self.mainstats = mainstats
        self.substats = substats
        self.lightcones = lightcones

def getDataAsList(data, pattern):
    arr = []
    matches = re.findall(pattern, data.get_attribute('textContent'))
    for match in matches:
            if match not in arr:
                arr.append(match.strip())
    return arr

def getSiteData(url, name):
    # PREPARE SELENIUM INSTANCE
    # ENABLE NO GUI SELENIUM
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    # INITIALIZE INSTANCE OF DRIVER
    driver = webdriver.Chrome(options=options)
    try:
        # VISIT TARGET SITE
        driver.get(url + name.lower())
        # GET INFORMATION FROM URL
        description = []
        # DESCRIPTION:
        description.append(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div/div[2]/div[2]/div[3]/div[1]/div[2]/div/h2/strong[4]').text)
        description.append(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div/div[2]/div[2]/div[3]/div[1]/div[2]/div/h2/strong[3]').text)
        # COLOR:
        color = driver.find_element(By.CSS_SELECTOR, 'strong.' + description[1]).value_of_css_property("color")
        rgba_values = [int(value) for value in color.replace('rgba(', '').replace(')', '').split(', ')]
        rgb_values = rgba_values[:3]
        color = Colour.from_rgb(*rgb_values)
        # list variables for all fields
        traces = []
        relics = []
        planetary = []
        mainstats = []
        lightcones = []
        
        # TRACES:
        # trace_elems = driver.find_elements(By.CLASS_NAME, 'sub-stats')
        trace_elems = driver.find_elements(By.XPATH, "//div[contains(@class, 'sub-stats')]")
        for elem in trace_elems:
            traces.append(elem.get_attribute('textContent').split(':', 1)[1])
        
        # RELICS & PLANETARY:        
        # relic_and_planetary_elems = driver.find_elements(By.CLASS_NAME, "relic-sets-rec")
        relic_and_planetary_elems = driver.find_elements(By.XPATH, "//div[contains(@class, 'relic-sets-rec')]")
        count = 1
        for elem in relic_and_planetary_elems:
            # print(elem.get_attribute('textContent'))
            output = elem.get_attribute('textContent')
            pattern = re.compile(r'<picture>.*?opacity=0\)\}\}', re.DOTALL)
            filtered_output = pattern.sub('', output)
            # index_of_2 is in all relics & planetary
            index_of_2 = filtered_output.find("(2)")
            # index_of_4 is only in relics
            index_of_4 = filtered_output.find("(4)")
            # index_of_plus is used to eliminate combinations
            index_of_plus = filtered_output.find("+")
            # edge case check to make sure only relics only start with a capital letter
            if filtered_output[0].isupper():
                continue
            # relic
            elif index_of_4 != -1 and index_of_plus == -1:
                filtered_output = filtered_output[1:index_of_2]
                if filtered_output not in relics:
                    relics.append(filtered_output)
            # 2 piece relic
            elif index_of_4 != -1 and index_of_plus != -1:
                # get 1st in 2 piece set
                substring_1_to_2 = re.search(r'\d(.*?)\(2\)', filtered_output).group(1)
                # get 2nd in 2 piece set
                substring_plus_to_2 = re.search(r'\.\+(.*?)\(2\)', filtered_output).group(1)
                if substring_1_to_2 not in relics:
                    relics.append(substring_1_to_2)
                if substring_plus_to_2 not in relics:
                    relics.append(substring_plus_to_2)
            # planetary
            else:
                filtered_output = filtered_output[1:index_of_2]
                planetary.append(filtered_output)       
        
        # MAINSTATS:
        # main_elems = driver.find_elements(By.CLASS_NAME, 'list-stats')
        main_elems = driver.find_elements(By.XPATH, "//div[contains(@class, 'list-stats')]")
        headers = ['Body', 'Feet', 'Sphere', 'Rope']
        # count used to only get stats for headers
        count = 0
        pattern_html = re.compile(r'<span.*?>(.*?)<\/span>', re.DOTALL)
        for elem in main_elems:
            if count < 4:
                output = elem.get_attribute('innerHTML')
                matches = re.findall(pattern_html, output)
                combined_string = ' | '.join(matches)
                mainstats.append(headers[count] + ': ' + combined_string)
                count = count + 1
            else:
                break
        # SUBSTATS:
        substats = traces[0]        
        
        # LIGHTCONES:
        # cone_elems = driver.find_elements(By.CLASS_NAME, 'detailed-cones')
        cone_elems = driver.find_elements(By.XPATH, "//div[contains(@class, 'detailed-cones')]")
        for elem in cone_elems:
            output = elem.get_attribute('innerText')
            # print(output)
            start_index = output.find('0)}}')
            end_index = output.find('(S')
            result = output[start_index+4:end_index+4]
            if result == '':
                break
            else:
                lightcones.append(result)

        # POPULATE THE CLASS INSTANCE
        embedData = EmbedData(name.capitalize(), description, color, traces, relics, 
                              planetary, mainstats, substats, lightcones)
        # STOP DRIVER
        driver.quit()
        return embedData
    except Exception as e:
        driver.quit()
        print(f"[ERROR]: {e}")

# /build command
    # takes one input
    # input: name of character that user wants to build
@tree.command(name="build", description="Build command: takes the input of the character that is typed to build")
async def build(interaction: discord.Interaction, character_name: str):
    # CHECK IF THE CHARACTER EXISTS (CHARACTER PAGE IS UP)
    url = 'https://www.prydwen.gg/star-rail/characters/'
    response = requests.get(url + character_name.lower())
    valid = False
    # IF STATUS CODE IS LESS THAN 400 THEN SITE IS VALID
    if response.status_code < 400:
        valid = True
    else:
        await interaction.response.send_message(f'ERROR: character does not exist')
        return
    
    # DEFERRED MESSAGE BC INTERACTION TAKES LONGER THAN 3 SECONDS TO GET CHARACTER INFORMATION
    await interaction.response.defer()
    data = getSiteData(url, character_name)
    # print(f"{data.title}'\n'{data.description}'\n'{data.traces}'\n'{data.planetary}'\n'{data.mainstats}'\n'{data.substats}'\n'{data.lightcones}")
    embed=discord.Embed(title=data.title, description=f"{data.description[0]}\n{data.description[1]}", color=data.color)
    embed.add_field(name='Trace Priority', value=f"{data.traces[1]}\n{data.traces[2]}", inline=False)
    embed.add_field(name='Relics & Stats', value=f"{chr(10).join(data.relics)}", inline=True)
    embed.add_field(name='Planetary Sets', value=f"{chr(10).join(data.planetary)}", inline=True)
    embed.add_field(name='Main Stat Priority', value=f"{chr(10).join(data.mainstats)}", inline=False)
    embed.add_field(name='Substat Priority', value=f"{data.substats}", inline=False)
    embed.add_field(name='Light Cones', value=f"{chr(10).join(data.lightcones)}", inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)



bot.run(TOKEN)