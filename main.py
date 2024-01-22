import re
import sys
import os
import time
import requests
import urllib


#Path where POE is installed
poe_log_file_path = "PATH_HERE"

#Whisper history
whisper_history_path = "whisper_history"

#Token api for smsapi.pl
token_api = "TOKEN_HERE"

#Phone number
phone_nr = 123456789

#Chaos and Divine trade value threshold
divine_min_trade_value=1
chaos_min_trade_value=100

def getTradeValue(whipser, currency_type):
	if currency_type == "divine":
		match = re.search(r"(for |for my )[0-9]{1,9} [Dd]ivine", whipser)
	else:
		match = re.search(r"(for |for my )[0-9]{1,9} [Cc]haos", whipser)
	if match:
		value_match = re.search(r"[0-9]{1,9}", match.group(0))
		return int(value_match.group(0))
	else:
		return 0

def cleanMessage(message):
	match = re.search(r"@From.*", message)
	if match:
		return match.group(0)[6:]
	else:
		return message

def sendNotification(message: str):
	params = {
				"sender": "POE Trade",
        "message": cleanMessage(message),
        "recipients": [
            {"msisdn": phone_nr}
        ],
	}
	response = requests.post("https://gatewayapi.com/rest/mtsms",
							json=params,
							auth=(token_api, ""))
	response.raise_for_status()
	print(response.json())

first_run = False

while True:
	time.sleep(1)
	f_log = open(poe_log_file_path, "r")

	if os.path.isfile(whisper_history_path):
		f_whispers = open(whisper_history_path, "r")
		old_whispers = f_whispers.read()
	else:
		f_whispers = open(whisper_history_path, "x")
		old_whispers = ""
		first_run = True

	f_whispers.close()

	last_line=""

	with open(poe_log_file_path, "rb") as file:
		try:
			file.seek(-2, os.SEEK_END)
			while file.read(1) != b'\n':
				file.seek(-2, os.SEEK_CUR)
		except OSError:
				file.seek(0)
		last_line = file.readline().decode()

	if not re.search(re.escape(last_line[0:37]), old_whispers):
		re.search("@From", last_line)
		print(last_line)
		f_whispers = open(whisper_history_path, "a")
		f_whispers.write(last_line)
		f_whispers.close()
		if first_run:
			continue
		trade_value_divine = getTradeValue(last_line, "divine")
		trade_value_chaos = getTradeValue(last_line, "chaos")
		print("Chaos: ", trade_value_chaos)
		print("Divine: ", trade_value_divine)
		if trade_value_chaos < chaos_min_trade_value and trade_value_divine < divine_min_trade_value:
			print("Lowball, skipping...")
		if trade_value_chaos >= chaos_min_trade_value or trade_value_divine >= divine_min_trade_value:
			sendNotification(last_line)
