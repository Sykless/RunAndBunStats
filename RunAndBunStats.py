from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask import Flask, request, jsonify
import pprint
# pip install google-api-python-client google-auth

BADGES = ["Knuckle Badge", "Stone Badge", "Dynamo Badge", "Balance Badge", "Heat Badge", "Feather Badge", "Mind Badge", "Rain Badge"]
STATS_NAMES = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"]

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

UPLOAD_BATCH_SIZE = 200

# Colors in API are 0..1 floats
COLOR_BLACK = {"red": 0, "green": 0, "blue": 0}
COLOR_GREY = {"red": 0.4, "green": 0.4, "blue": 0.4}
COLOR_CYAN = {"red": 0, "green": 1, "blue": 1}
COLOR_RED = {"red": 1, "green": 0, "blue": 0}

driveCredentials = service_account.Credentials.from_service_account_file(
    "service-account.json",
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
)

sheetsService = build('sheets', 'v4', credentials = driveCredentials)
driveService = build('drive', 'v3', credentials = driveCredentials)
flaskApp = Flask(__name__)

MERGE = 1
BOLD = 2
CENTER = 3
FONT_CYAN = 4
FONT_RED = 5
BACKGROUND_GREY = 6
BACKGROUND_BLACK = 7
FORMULA = 8

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

    if CENTER in options:
        userEnteredFormat["horizontalAlignment"] = "CENTER"
        fields += ",horizontalAlignment"

    if BACKGROUND_GREY in options:
        userEnteredFormat["backgroundColor"] = COLOR_GREY
        fields += ",backgroundColor"

    elif BACKGROUND_BLACK in options:
        userEnteredFormat["backgroundColor"] = COLOR_BLACK
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


def generateRunCard(requests, sheetId, runId):
    startRow = 18 * runId

    # Helper to convert a relative inside-run row/col to absolute indices
    def abs_range(rel_row_start, rel_row_end, rel_col_start, rel_col_end):
        return {
            "sheetId": sheetId,
            "startRowIndex": startRow + rel_row_start,
            "endRowIndex": startRow + rel_row_end,
            "startColumnIndex": rel_col_start,
            "endColumnIndex": rel_col_end
        }
    
    # Update column sizes
    updateColumnSize(requests, sheetId, 21, 0)
    updateColumnSize(requests, sheetId, 55, 1, 8)
    updateColumnSize(requests, sheetId, 21, 9)

    # Left/right white separator, merge all cells vertically 
    mergeCells(requests, abs_range(2, 17, 0, 1))
    mergeCells(requests, abs_range(2, 17, 9, 10))
    
    # Top grey line, merge all cells horizontally
    setCellContent(requests, abs_range(0, 1, 0, 500), "", options = [MERGE, BACKGROUND_GREY])

    # Top white line, merge all cells horizontally
    mergeCells(requests, abs_range(1, 2, 0, 500))

    # Run number
    setCellContent(requests, abs_range(2, 3, 1, 9), f"Run #{runId}", options = [MERGE, BOLD, CENTER, FONT_CYAN, BACKGROUND_GREY])

    # Run start date
    setCellContent(requests, abs_range(3, 4, 1, 5), "Run start", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(3, 4, 5, 9), "DD/MM/YYYY hh:mm", options = [MERGE, CENTER])

    # Run end date
    setCellContent(requests, abs_range(4, 5, 1, 5), "Run end", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(4, 5, 5, 9), "DD/MM/YYYY hh:mm", options = [MERGE, CENTER])

    # Run end date
    setCellContent(requests, abs_range(5, 6, 1, 5), "Won battles", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(5, 6, 5, 9), "123/456", options = [MERGE, CENTER])

    # Dead Pokémon
    setCellContent(requests, abs_range(6, 7, 1, 5), "Dead Pokémon", options = [MERGE, BOLD, CENTER])
    setCellContent(requests, abs_range(6, 7, 5, 9), "4/26", options = [MERGE, CENTER])

    # White separator, merge all cells horizontally 
    mergeCells(requests, abs_range(7, 8, 1, 9))

    # Gym Badges label
    setCellContent(requests, abs_range(8, 9, 1, 9), "Gym Badges", options = [MERGE, BOLD, CENTER])

    # Gym Badges sprites
    for col in range(8):
        setCellContent(requests, abs_range(9, 11, col + 1, col + 2), f'=VLOOKUP("{BADGES[col]}",Sprites!$A:$B,2,FALSE)', options = [MERGE, CENTER, FORMULA])

    # White separator, merge all cells horizontally 
    mergeCells(requests, abs_range(11, 12, 1, 9))

    # Personal Best Trainer Name
    setCellContent(requests, abs_range(12, 13, 1, 9), "", options = [MERGE, CENTER])
    setCellBoldSplitContent(requests, abs_range(12, 13, 1, 9), "Personal Best : ", "Leader Archie")

    # Merge trainer team separators
    for row in [1,4,8]:
        mergeCells(requests, abs_range(13, 17, row, row + 1))

    # Personal Best Trainer Sprite
    setCellContent(requests, abs_range(13, 17, 2, 4), '=VLOOKUP("TRAINER_PIC_AQUA_LEADER_ARCHIE",Sprites!$A:$B,2,FALSE)', options = [MERGE, CENTER, FORMULA])

    # Personal Best Trainer Team Sprite top
    for i in range(3):
        setCellContent(requests, abs_range(13, 15, 5 + i, 6 + i), '=VLOOKUP(390,Sprites!$A:$B,2,FALSE)', options = [MERGE, CENTER, FORMULA])

    # Personal Best Trainer Team Sprite bottom
    for i in range(3):
        setCellContent(requests, abs_range(15, 17, 5 + i, 6 + i), '=VLOOKUP(390,Sprites!$A:$B,2,FALSE)', options = [MERGE, CENTER, FORMULA])

    # Bottom white line, merge all cells horizontally
    mergeCells(requests, abs_range(17, 18, 0, 500))

    # Bottom grey line, merge all cells horizontally
    setCellContent(requests, abs_range(18, 19, 0, 500), "", options = [MERGE, BACKGROUND_GREY])

    # Add borders
    addBorders(requests, abs_range(2,17,1,9))



def generatePokemonCard(requests, sheetId, pokemon, zone, runId, pokemonId):
    startRow = 18 * runId + 2
    startColumn = 10 + 5 * pokemonId

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
    addBorders(requests, abs_range(0,15,0,4))

    # Right white separator, merge all cells vertically 
    mergeCells(requests, abs_range(0, 15, 4, 5))

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
        setCellContent(requests, abs_range(6, 7, 2, 4), f"Level {pokemon["level"]}", options = [MERGE, CENTER])

        # White separator, merge all cells horizontally
        mergeCells(requests, abs_range(7, 8, 0, 4))

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
            setCellContent(requests, abs_range(12 + i % 3, 13 + i % 3, 2*(i // 3), 1 + 2*(i // 3)), STATS_NAMES[i], options = [CENTER])
            setCellContent(requests, abs_range(12 + i % 3, 13 + i % 3, 1 + 2*(i // 3), 2 + 2*(i // 3)), pokemon["IVs"][i], options = [CENTER, FONT_RED if i in [statBuffed, statDebuffed] else None,
                                                                                                                                      BOLD if i == statBuffed else None])
    
    # No Pokémon caught in the zone : merge all cells
    else:
        mergeCells(requests, abs_range(1, 15, 0, 4))
        emptyCell(requests, abs_range(1, 2, 0, 1))



@flaskApp.route("/initRun", methods = ["POST"])
def initRun():
    requests = []
    runNumber = 0
    
    try:
        # Convert provided data to JSON
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Generate the run card
        generateRunCard(requests, data["keys"]["spreadsheet"]["sheetId"], runNumber)

        # Generate an empty card for each zone
        for i, (zone, pokemon) in enumerate(data["pokemonData"].items()):
            generatePokemonCard(requests, data["keys"]["spreadsheet"]["sheetId"], pokemon, zone, runNumber, i)

        # Execute the requests divided into chunks
        for chunkStart in range(0, len(requests), UPLOAD_BATCH_SIZE):
            chunk = requests[chunkStart : chunkStart + UPLOAD_BATCH_SIZE]

            # Upload requests to Google Sheets API
            reponse = sheetsService.spreadsheets().batchUpdate(
                spreadsheetId = data["keys"]["spreadsheet"]["spreadsheetId"],
                body = {"requests": chunk}).execute()

        # Return success
        return jsonify({"message": "Data received successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500



@flaskApp.route("/updatePokemonCards", methods = ["POST"])
def updatePokemonCards():
    requests = []
    runNumber = 0
    
    try:
        # Convert provided data to JSON
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Read all Pokemon cards zones in Sheet
        result = sheetsService.spreadsheets().values().get(
            spreadsheetId = data["keys"]["spreadsheet"]["spreadsheetId"],
            range = f"Runs!K{3 + 18 * runNumber}:{3 + 18 * runNumber}"
        ).execute()

        # Convert zones data to list
        zoneList = [zoneName for zoneName in result.get("values", [[None]])[0] if zoneName]

        # Iterate over each zone
        for columnId in range(len(zoneList)):
            zone = zoneList[columnId]
            
            # Update provided zones
            if (zone in data["pokemonData"]):
                generatePokemonCard(requests, data["keys"]["spreadsheet"]["sheetId"], data["pokemonData"][zone], zone, runNumber, columnId)

        # Execute the requests divided into chunks
        for chunkStart in range(0, len(requests), UPLOAD_BATCH_SIZE):
            chunk = requests[chunkStart : chunkStart + UPLOAD_BATCH_SIZE]
            
            # Upload requests to Google Sheets API
            reponse = sheetsService.spreadsheets().batchUpdate(
                spreadsheetId = data["keys"]["spreadsheet"]["spreadsheetId"],
                body = {"requests": chunk}).execute()

        # Return success
        return jsonify({"message": "Data received successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    flaskApp.run(host = "0.0.0.0", port = 5000)