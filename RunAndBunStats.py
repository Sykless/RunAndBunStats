from google.auth import default
from googleapiclient.discovery import build
from flask import Flask, request, jsonify
import traceback
import os

ZONES = ["Starter", "Littleroot Town", "Route 101", "Oldale Town", "Route 103", "Route 102", "Petalburg City", "Route 104", "Dewford Town", "Route 107", "Route 106", "Granite Cave", "Route 109", "Slateport City", "Route 110", "Petalburg Woods", "Rustboro City", "Route 115", "Route 116", "Rusturf Tunnel", "Verdanturf Town", "Route 117", "Mauville City", "Route 111", "Route 118", "Altering Cave", "Mirage Tower", "Route 113", "Fallarbor Town", "Desert Underpass", "Route 114", "Meteor Falls", "Route 112", "Fiery Path", "Mt. Chimney", "Jagged Pass", "Lavaridge Town", "Route 134", "New Mauville", "Route 105", "Route 108", "Abandoned Ship", "Route 119", "Fortree City", "Route 120", "Scorched Slab", "Route 121", "Safari Zone", "Lilycove City", "Route 122", "Route 123", "Mt. Pyre", "Magma Hideout", "Aqua Hideout", "Route 124", "Mossdeep City", "Route 125", "Shoal Cave", "Route 127", "Route 124 Underwater", "Route 126", "Route 126 Underwater", "Sootopolis City", "Route 128", "Route 129", "Ever Grande City", "Seafloor Cavern", "Cave of Origin", "Route 130", "Route 131", "Pacifidlog Town", "Route 132", "Route 133", "Sky Pillar", "Victory Road"]
BADGES = ["Knuckle Badge", "Stone Badge", "Dynamo Badge", "Balance Badge", "Heat Badge", "Feather Badge", "Mind Badge", "Rain Badge"]
STATS_NAMES = {
    "EN": ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"],
    "FR": ["PV", "Attaque", "Défense", "Atq. Spé", "Def. Spé", "Vitesse"]
}

NATURE_DICO_FR = {
    "Adamant": "Rigide",
    "Bashful": "Pudique",
    "Bold": "Assuré",
    "Brave": "Brave",
    "Calm": "Calme",
    "Careful": "Prudent",
    "Docile": "Docile",
    "Gentle": "Gentil",
    "Hardy": "Hardi",
    "Hasty": "Pressé",
    "Impish": "Malin",
    "Jolly": "Jovial",
    "Lax": "Lâche",
    "Lonely": "Solo",
    "Mild": "Doux",
    "Modest": "Modeste",
    "Naive": "Naïf",
    "Naughty": "Mauvais",
    "Quiet": "Discret",
    "Quirky": "Bizarre",
    "Rash": "Foufou",
    "Relaxed": "Relax",
    "Sassy": "Malpoli",
    "Serious": "Sérieux",
    "Timid": "Timide"
}

NATURE_DICO = {
    "Hardy": [None, None],
    "Lonely": [1, 2],
    "Brave": [1, 5],
    "Adamant": [1, 3],
    "Naughty": [1, 4],
	"Bold": [2, 1],
    "Docile": [None, None],
    "Relaxed": [2, 5],
    "Impish": [2, 3],
    "Lax": [2, 4],
	"Timid": [5, 1],
    "Hasty": [5, 2],
    "Serious": [None, None],
    "Jolly": [5, 3],
    "Naive": [5, 4],
	"Modest": [3, 1],
    "Mild": [3, 2],
    "Quiet": [3, 5],
    "Bashful": [None, None],
    "Rash": [3, 4],
	"Calm": [4, 1],
    "Gentle": [4, 2],
    "Sassy": [4, 5],
    "Careful": [4, 3],
    "Quirky": [None, None]
}

# Setup NATURE_DICO with french Nature values
for english, french in NATURE_DICO_FR.items():
    NATURE_DICO[french] = NATURE_DICO[english]

API_PASSWORD = os.getenv("API_PASSWORD", "")
UPLOAD_BATCH_SIZE = 200

# Colors in API are 0..1 floats
COLOR_WHITE = {"red": 1, "green": 1, "blue": 1}
COLOR_BLACK = {"red": 0, "green": 0, "blue": 0}
COLOR_GREY = {"red": 0.4, "green": 0.4, "blue": 0.4}
COLOR_LIGHTGREY = {"red": 0.95, "green": 0.95, "blue": 0.95}
COLOR_CYAN = {"red": 0, "green": 1, "blue": 1}
COLOR_RED = {"red": 1, "green": 0, "blue": 0}
COLOR_LIGHTRED = {"red": 1, "green": 0.5, "blue": 0.5}

credentials, project = default(scopes = ['https://www.googleapis.com/auth/spreadsheets'])
sheetsService = build('sheets', 'v4', credentials = credentials)
flaskApp = Flask(__name__)

MERGE = 1
BOLD = 2
CENTER = 3
FONT_CYAN = 4
FONT_RED = 5
FONT_LIGHTRED = 6
FONT_WHITE = 7
BACKGROUND_GREY = 8
BACKGROUND_LIGHTGREY = 9
BACKGROUND_BLACK = 10
FORMULA = 11

def missingMandatoryKeys(data):
    mandatoryKeys = {
        "keys.spreadsheetId": data.get("keys", {}).get("spreadsheetId"),
        "keys.sheetId": data.get("keys", {}).get("sheetId"),
        "updatedData.runs": data.get("updatedData", {}).get("runs"),
        "fullData.runs": data.get("fullData", {}).get("runs"),
        "lang": data.get("lang")
    }

    for keyName, keyValue in mandatoryKeys.items():
        if (not keyValue):
            print(f"❌ Missing parameter {keyName}")
            return keyValue
        
    # No missing keys
    return None
        

def containsOutdatedKeys(data):
    outdatedKeys = ["newRuns", "numberOfRuns"]

    for key in outdatedKeys:
        if key in data.get("updatedData", {}):
            return True
        
    # No outdated key
    return False
    

def mergeCells(requests, range):
    requests.append({"mergeCells": {"range": range, "mergeType": "MERGE_ALL"}})

def unmergeCells(requests, range):
    requests.append({"unmergeCells": {"range": range}})

def setCellContent(requests, range, cellContent, options = []):
    userEnteredFormat = {"textFormat": {}}
    fields = "userEnteredValue,userEnteredFormat(textFormat"
    userEnteredValue = {}

    if MERGE in options:
        mergeCells(requests, range)

    if BOLD in options:
        userEnteredFormat["textFormat"]["bold"] = True

    if FONT_CYAN in options:
        userEnteredFormat["textFormat"]["foregroundColor"] = COLOR_CYAN

    elif FONT_RED in options:
        userEnteredFormat["textFormat"]["foregroundColor"] = COLOR_RED

    elif FONT_LIGHTRED in options:
        userEnteredFormat["textFormat"]["foregroundColor"] = COLOR_LIGHTRED

    elif FONT_WHITE in options:
        userEnteredFormat["textFormat"]["foregroundColor"] = COLOR_WHITE

    if CENTER in options:
        userEnteredFormat["horizontalAlignment"] = "CENTER"
        fields += ",horizontalAlignment"

    if BACKGROUND_GREY in options:
        userEnteredFormat["backgroundColor"] = COLOR_GREY
        fields += ",backgroundColor"

    elif BACKGROUND_BLACK in options:
        userEnteredFormat["backgroundColor"] = COLOR_BLACK
        fields += ",backgroundColor"

    elif BACKGROUND_LIGHTGREY in options:
        userEnteredFormat["backgroundColor"] = COLOR_LIGHTGREY
        fields += ",backgroundColor"

    if FORMULA in options:
        userEnteredValue["formulaValue"] = cellContent
    else:
        userEnteredValue["stringValue"] = cellContent

    requests.append({
        "repeatCell": {
            "range": range,
            "cell": {
                "userEnteredValue": userEnteredValue,
                "userEnteredFormat": userEnteredFormat
            },
            "fields": fields + ")"
        }
    })

def setCellBoldSplitContent(requests, range, boldString, regularString):
    requests.append({
        "updateCells": {
            "range": range,
            "rows": [
                {
                    "values": [
                        {
                            "userEnteredValue": {"stringValue": f"{boldString} {regularString}"},
                            "textFormatRuns": [
                                {"startIndex": 0, "format": {"bold": True}},
                                {"startIndex": len(boldString), "format": {"bold": False}}
                            ]
                        }
                    ]
                }
            ],
            "fields": "userEnteredValue,textFormatRuns"
        }
    })

def emptyCell(requests, range):
    requests.append({
        "repeatCell": {
            "range": range,
            "cell": { "userEnteredValue": None },
            "fields": "userEnteredValue"
        }
    })

def clearFormatting(requests, range):
    requests.append({
        "repeatCell": {
            "range": range,
            "cell": {"userEnteredFormat": {}},
            "fields": "userEnteredFormat"
        }
    })

def updateColumnSize(requests, sheetId, columnSize, columnId, columnNumbers = 1):
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheetId, "dimension": "COLUMNS", "startIndex": columnId, "endIndex": columnId + columnNumbers},
            "properties": {"pixelSize": columnSize},
            "fields": "pixelSize"
        }
    })

def addBorders(requests, range):
    requests.append({
        "updateBorders": {
            "range": range,
            "top": {"style": "SOLID", "width": 1, "color": COLOR_BLACK},
            "bottom": {"style": "SOLID", "width": 1, "color": COLOR_BLACK},
            "left": {"style": "SOLID", "width": 1, "color": COLOR_BLACK},
            "right": {"style": "SOLID", "width": 1,"color": COLOR_BLACK},
        }
    })

def insertRows(requests, sheetId, numberOfRows):
    requests.append({
        "insertDimension": {
            "range": {
                "sheetId": sheetId,
                "dimension": "ROWS",
                "startIndex": 0,
                "endIndex": numberOfRows
            }
        }
    })


def generateRunCard(requests, sheetId, runId, runData, lang):
    startRow = 0

    # Helper to convert a relative inside-run row/col to absolute indices
    def abs_range(rel_row_start, rel_row_end, rel_col_start, rel_col_end):
        return {
            "sheetId": sheetId,
            "startRowIndex": startRow + rel_row_start,
            "endRowIndex": startRow + rel_row_end,
            "startColumnIndex": rel_col_start,
            "endColumnIndex": rel_col_end
        }
    
    # Insert 18 rows and clear formatting to make place for the new run
    insertRows(requests, sheetId, 18)
    clearFormatting(requests, abs_range(1, 18, 0, 500))
    
    # Update column sizes
    updateColumnSize(requests, sheetId, 21, 0)
    updateColumnSize(requests, sheetId, 55, 1, 8)
    updateColumnSize(requests, sheetId, 21, 9)

    # Left/right white separator, merge all cells vertically 
    setCellContent(requests, abs_range(2, 17, 0, 1), "", options = [MERGE, BACKGROUND_LIGHTGREY])
    setCellContent(requests, abs_range(2, 17, 9, 10), "", options = [MERGE, BACKGROUND_LIGHTGREY])
    
    # Top grey line, merge all cells horizontally
    setCellContent(requests, abs_range(0, 1, 0, 500), "", options = [MERGE, BACKGROUND_GREY])

    # Top white line, merge all cells horizontally
    setCellContent(requests, abs_range(1, 2, 0, 500), "", options = [MERGE, BACKGROUND_LIGHTGREY])

    # Run number
    setCellContent(requests, abs_range(2, 3, 1, 9), 
                   '=IFERROR("Run #" & (1 + VALUE(REGEXEXTRACT(INDIRECT("B" & ROW() + 18), "\\d+"))), "Run #1")',
                   options = [MERGE, BOLD, CENTER, FONT_CYAN, BACKGROUND_GREY, FORMULA])

    # Run start date
    setCellContent(requests, abs_range(3, 4, 1, 5), "Début de la run" if lang == "FR" else "Run start", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(3, 4, 5, 9), runData["runStart"], options = [MERGE, CENTER])

    # Run end date
    setCellContent(requests, abs_range(4, 5, 1, 5), "Fin de la run" if lang == "FR" else "Run end", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(4, 5, 5, 9), runData["runEnd"], options = [MERGE, CENTER])

    # Run end date
    setCellContent(requests, abs_range(5, 6, 1, 5), "Combats gagnés" if lang == "FR" else "Won battles", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(5, 6, 5, 9), runData["wonBattles"], options = [MERGE, CENTER])

    # Dead Pokémon
    setCellContent(requests, abs_range(6, 7, 1, 5), "Pokémons morts" if lang == "FR" else "Dead Pokémon", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(6, 7, 5, 9), runData["deadPokemon"], options = [MERGE, CENTER])

    # White separator, merge all cells horizontally, hide runId in white font
    setCellContent(requests, abs_range(7, 8, 1, 9), f"RundId : {runId}", options = [MERGE, CENTER, FONT_WHITE])

    # Gym Badges label
    setCellContent(requests, abs_range(8, 9, 1, 9), "Badges" if lang == "FR" else "Gym Badges", options = [MERGE, BOLD, CENTER])

    # Gym Badges sprites
    for i in range(8):
        setCellContent(requests, abs_range(9, 11, i + 1, i + 2), 
                       f'=VLOOKUP("{BADGES[i]}",Sprites!$A:$B,2,FALSE)' if i < runData["gymBadges"] else "",
                       options = [MERGE, CENTER, FORMULA if i < runData["gymBadges"] else None])

    # White separator, merge all cells horizontally 
    mergeCells(requests, abs_range(11, 12, 1, 9))

    # Personal Best Trainer Name
    setCellContent(requests, abs_range(12, 13, 1, 9), "", options = [MERGE, CENTER])
    setCellBoldSplitContent(requests, abs_range(12, 13, 1, 9), "Personal Best : ", runData["personalBest"]["trainerName"])

    # Merge trainer team separators
    for row in [1,4,8]:
        mergeCells(requests, abs_range(13, 17, row, row + 1))

    # Personal Best Trainer Sprite
    setCellContent(requests, abs_range(13, 17, 2, 4), f'=VLOOKUP("{runData["personalBest"]["trainerSprite"]}",Sprites!$A:$B,2,FALSE)', options = [MERGE, CENTER, FORMULA])

    # Personal Best Trainer Team Sprite top
    for i in range(3):
        setCellContent(requests, abs_range(13, 15, 5 + i, 6 + i), 
                    f'=VLOOKUP({runData["personalBest"]["trainerTeam"][i]},Sprites!$A:$B,2,FALSE)' if i < len(runData["personalBest"]["trainerTeam"]) else "",
                    options = [MERGE, CENTER, FORMULA if i < len(runData["personalBest"]["trainerTeam"]) else None])

    # Personal Best Trainer Team Sprite bottom
    for i in range(3):
        setCellContent(requests, abs_range(15, 17, 5 + i, 6 + i), 
                    f'=VLOOKUP({runData["personalBest"]["trainerTeam"][i + 3]},Sprites!$A:$B,2,FALSE)' if i + 3 < len(runData["personalBest"]["trainerTeam"]) else "",
                    options = [MERGE, CENTER, FORMULA if i + 3 < len(runData["personalBest"]["trainerTeam"]) else None])

    # Bottom white line, merge all cells horizontally
    setCellContent(requests, abs_range(17, 18, 0, 500), "", options = [MERGE, BACKGROUND_LIGHTGREY])

    # Bottom grey line, merge all cells horizontally
    setCellContent(requests, abs_range(18, 19, 0, 500), "", options = [MERGE, BACKGROUND_GREY])

    # Add borders
    addBorders(requests, abs_range(2,17,1,9))



def updateRunCard(requests, sheetId, runCardId, runData):
    startRow = 18 * runCardId

    # Helper to convert a relative inside-run row/col to absolute indices
    def abs_range(rel_row_start, rel_row_end, rel_col_start, rel_col_end):
        return {
            "sheetId": sheetId,
            "startRowIndex": startRow + rel_row_start,
            "endRowIndex": startRow + rel_row_end,
            "startColumnIndex": rel_col_start,
            "endColumnIndex": rel_col_end
        }

    # Run start date
    if "runStart" in runData: setCellContent(requests, abs_range(3, 4, 5, 9), runData["runStart"], options = [CENTER])

    # Run end date
    if "runEnd" in runData: setCellContent(requests, abs_range(4, 5, 5, 9), runData["runEnd"], options = [CENTER])

    # Run end date
    if "wonBattles" in runData: setCellContent(requests, abs_range(5, 6, 5, 9), runData["wonBattles"], options = [CENTER])

    # Dead Pokémon
    if "deadPokemon" in runData: setCellContent(requests, abs_range(6, 7, 5, 9), runData["deadPokemon"], options = [CENTER])

    # Gym Badges sprites
    for col in range(runData["gymBadges"] if "gymBadges" in runData else 0):
        setCellContent(requests, abs_range(9, 11, col + 1, col + 2), f'=VLOOKUP("{BADGES[col]}",Sprites!$A:$B,2,FALSE)', options = [CENTER, FORMULA])

    # Personal Best
    if "personalBest" in runData:

        # Personal Best Trainer Name
        setCellBoldSplitContent(requests, abs_range(12, 13, 1, 9), "Personal Best : ", runData["personalBest"]["trainerName"])

        # Personal Best Trainer Sprite
        setCellContent(requests, abs_range(13, 17, 2, 4), f'=VLOOKUP("{runData["personalBest"]["trainerSprite"]}",Sprites!$A:$B,2,FALSE)', options = [CENTER, FORMULA])

        # Personal Best Trainer Team Sprite top
        for i in range(3):
            setCellContent(requests, abs_range(13, 15, 5 + i, 6 + i), 
                        f'=VLOOKUP({runData["personalBest"]["trainerTeam"][i]},Sprites!$A:$B,2,FALSE)' if i < len(runData["personalBest"]["trainerTeam"]) else "",
                        options = [CENTER, FORMULA if i < len(runData["personalBest"]["trainerTeam"]) else None])

        # Personal Best Trainer Team Sprite bottom
        for i in range(3):
            setCellContent(requests, abs_range(15, 17, 5 + i, 6 + i), 
                        f'=VLOOKUP({runData["personalBest"]["trainerTeam"][i + 3]},Sprites!$A:$B,2,FALSE)' if i + 3 < len(runData["personalBest"]["trainerTeam"]) else "",
                        options = [CENTER, FORMULA if i + 3 < len(runData["personalBest"]["trainerTeam"]) else None])



def generatePokemonCard(requests, sheetId, pokemon, zone, runCardId, pokemonCardId, lang):
    startRow = 18 * runCardId + 2
    startColumn = 10 + 5 * pokemonCardId

    # Helper to convert a relative inside-run row/col to absolute indices
    def abs_range(rel_row_start, rel_row_end, rel_col_start, rel_col_end):
        return {
            "sheetId": sheetId,
            "startRowIndex": startRow + rel_row_start,
            "endRowIndex": startRow + rel_row_end,
            "startColumnIndex": startColumn + rel_col_start,
            "endColumnIndex": startColumn + rel_col_end
        }
    
    # Update column sizes
    updateColumnSize(requests, sheetId, 75, startColumn)
    updateColumnSize(requests, sheetId, 21, startColumn + 1)
    updateColumnSize(requests, sheetId, 75, startColumn + 2)
    updateColumnSize(requests, sheetId, 21, startColumn + 3, 2)

    # Add borders
    addBorders(requests, abs_range(0, 15, 0, 4))

    # Right white separator, merge all cells vertically 
    setCellContent(requests, abs_range(0, 15, 4, 5), "", options = [MERGE, BACKGROUND_LIGHTGREY])

    # Zone name
    setCellContent(requests, abs_range(0, 1, 0, 4), zone, options = [MERGE, BOLD, CENTER, FONT_CYAN, BACKGROUND_GREY])

    # Reset Pokémon card by unmerging all cells
    unmergeCells(requests, abs_range(1, 15, 0, 4))

    # Pokémon caught in the zone : display all Pokémon data
    if pokemon:

        # Pokémon sprite
        setCellContent(requests, abs_range(1, 5, 0, 4), f"=VLOOKUP({pokemon["pokedexId"]},Sprites!$A:$B,2,FALSE)", options = [MERGE, CENTER, FORMULA])

        # Pokémon name + nickname
        unmergeCells(requests, abs_range(5, 6, 0, 4))
        setCellContent(requests, abs_range(5, 6, 0, 3 + pokemon["alive"]), "", options = [MERGE, CENTER])
        setCellBoldSplitContent(requests, abs_range(5, 6, 0, 3 + pokemon["alive"]), pokemon["nickname"], f"({pokemon["pokemonName"]})")

        # Dead emoji
        if (not pokemon["alive"]):
            setCellContent(requests, abs_range(5, 6, 3, 4), "💀", options = [CENTER, BACKGROUND_BLACK])

        # Ability
        setCellContent(requests, abs_range(6, 7, 0, 2), pokemon["ability"], options = [MERGE, CENTER])

        # Level
        setCellContent(requests, abs_range(6, 7, 2, 4),  f"{"Niveau" if lang == "FR" else "Level"} {pokemon["level"]}", options = [MERGE, CENTER])

        # White separator, merge all cells horizontally, hide PID in white font
        setCellContent(requests, abs_range(7, 8, 0, 4), f"{pokemon["pid"]}", options = [MERGE, CENTER, FONT_WHITE])

        # Moves
        for i in range(4):
            setCellContent(requests, abs_range(8 + i // 2, 9 + i // 2, 2*(i % 2), 2 + 2*(i % 2)), pokemon["moves"][i], options = [MERGE, CENTER])

        # White separator, merge all cells horizontally
        mergeCells(requests, abs_range(10, 11, 0, 4))

        # Nature
        setCellContent(requests, abs_range(11, 12, 0, 4), pokemon["nature"], options = [BOLD, MERGE, CENTER])

        # Stats
        statBuffed, statDebuffed = NATURE_DICO[pokemon["nature"]]

        for i in range(6):
            setCellContent(requests, abs_range(12 + i % 3, 13 + i % 3, 2*(i // 3), 1 + 2*(i // 3)), STATS_NAMES[lang][i], options = [CENTER])
            setCellContent(requests, abs_range(12 + i % 3, 13 + i % 3, 1 + 2*(i // 3), 2 + 2*(i // 3)), pokemon["IVs"][i], options = [CENTER, FONT_LIGHTRED if i == statDebuffed else None,
                                                                                                                                      FONT_RED if i == statBuffed else None, BOLD if i == statBuffed else None])
    
    # No Pokémon caught in the zone : merge all cells
    else:
        mergeCells(requests, abs_range(1, 15, 0, 4))
        emptyCell(requests, abs_range(1, 2, 0, 1))


def getRunCardId(runId, spreadsheetId):

    # Retrieve all strings in column B
    column = sheetsService.spreadsheets().values().get(
        spreadsheetId = spreadsheetId,
        range = "B:B"
    ).execute().get("values", [])

    # Iterate on each to find a run with provided runId
    for rowIndex, row in enumerate(column, start = 1):
        
        # Check only rows starting with "runId :"
        if row and row[0].startswith("RundId : "):

            # Extract the runId after the prefix
            parsedRunId = row[0].split("RundId : ", 1)[1].strip()

            # Calculate runCardId (0 : first card)
            if parsedRunId == runId:
                return int((rowIndex - 8) / 18)

    # Default : runCardId = -1 (no run found) 
    return -1

# Webapp root
@flaskApp.route("/", methods=["GET"])
def home():
    return "Run&BunStats en cours d'exécution..."


# Check password on protected routes
@flaskApp.before_request
def require_auth():
    protectedRoutes = ["/updateRun"]

    # Check the 'Authorization' header for a simple password
    if request.path in protectedRoutes:
        auth = request.headers.get("Authorization")

        if not auth or auth != f"Bearer {API_PASSWORD}":
            return jsonify({"error": "Unauthorized"}), 401


# Update each provided run and caught Pokemon
@flaskApp.route("/updateRun", methods = ["POST"])
def updateRun():
    requests = []
    
    try:
        # Convert provided data to JSON
        data = request.get_json()

        # No data received
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        # Outdated parameters
        if containsOutdatedKeys(data):
            return jsonify({"error": "Outdated version : please download the latest RunAndBunDisplay version https://github.com/Sykless/RunAndBunDisplay/releases"}), 400

        # Missing required fields
        missingKey = missingMandatoryKeys(data)
        if missingKey:
            return jsonify({"error": f"Missing required fields : {missingKey}"}), 400
        
        spreadsheetId = data["keys"]["spreadsheetId"]
        sheetId = data["keys"]["sheetId"]
        updatedData = data["updatedData"]["runs"]
        fullData = data["fullData"]["runs"]
        lang = data["lang"]

        # Iterate on each updated run and update run/pokemon cards
        for runId, run in updatedData.items():

            # Search for runId to find runCardId
            runCardId = getRunCardId(runId, spreadsheetId)

            # No run found : create the new run
            if (runCardId == -1):
                runCardId = 0

                # Insert a new run card
                generateRunCard(requests, sheetId, runId, fullData[runId]["runData"], lang)

                # Insert a Pokémon card for each zone
                for i in range(len(ZONES)):
                    zone = ZONES[i]
                    pokemon = fullData[runId]["pokemonData"][zone] if zone in fullData[runId]["pokemonData"] else None

                    # Generate a Pokémon card with Pokémon data if provided
                    generatePokemonCard(requests, sheetId, pokemon, zone, 0, i, lang)

            # RunId found : update row
            else:

                # If runData has parameters to update, update them
                if (run["runData"]):
                    updateRunCard(requests, sheetId, runCardId, run["runData"])

                # Iterate on each Pokémon and update cards
                for zone, pokemon in run["pokemonData"].items():

                    # Calculate pokemon card id from zone order (0 : first card)
                    pokemonCardId = ZONES.index(zone)

                    # Update/create Pokémon card with provided Pokémon data
                    generatePokemonCard(requests, sheetId, pokemon, zone, runCardId, pokemonCardId, lang)

        # Execute the requests divided into chunks
        for chunkStart in range(0, len(requests), UPLOAD_BATCH_SIZE):
            chunk = requests[chunkStart : chunkStart + UPLOAD_BATCH_SIZE]

            # Upload requests to Google Sheets API
            reponse = sheetsService.spreadsheets().batchUpdate(
                spreadsheetId = spreadsheetId,
                body = {"requests": chunk}).execute()

        # Return success
        return jsonify({"message": "Data received successfully"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Start server
if __name__ == "__main__":
    flaskApp.run(host = "0.0.0.0", port = int(os.environ.get("PORT", 8080)))
