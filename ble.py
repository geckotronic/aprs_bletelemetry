import os
import json
from datetime import datetime
from socket import *

interestData = {}
interestData["AC233FABAA22"] = {"pre":"S3"}
interestData["AC233FA20060"] = {"pre":"E8A"}
interestData["AC233FA196FC"] = {"pre":"E8C"}
interestData["A4C138000CAA"] = {"pre":"XTH"}

# Extrae solo ultimos datos de beacons de interes
def extractOnlyInterest(dataJson):
	global interestData
	devices = interestData.keys()
	dataShort = {}
	for dataItem in dataJson:
		if dataItem["mac"] in devices:
			if dataItem["mac"] in dataShort.keys():
				if "rawData" in dataShort[dataItem["mac"]].keys():
					if len(dataShort[dataItem["mac"]]["rawData"])<30:
						dataShort[dataItem["mac"]].pop("rawData")
				#Update only new fields 
				existingFields = set(dataShort[dataItem["mac"]]).intersection(set(dataItem))
				existingFields.discard("mac")
				for duplicate in existingFields:
					dataItem.pop(duplicate)
				dataShort[dataItem["mac"]].update(dataItem)
			else:
				dataShort[dataItem["mac"]] = dataItem
	return dataShort 

# Parsea data hexadecimal de interes 
def parsingData(dataPre):
	global interestData
	dataAll = {}
	dataAll["AC"] = 0
	dataAll["CD"] = 0
	for dataItem in dataPre.keys():
		if interestData[dataItem]["pre"] == "S3": 
			dataAll["TInterna"] = dataPre[dataItem]["temperature"] 
			dataAll["HInterna"] = dataPre[dataItem]["humidity"] 
		if interestData[dataItem]["pre"] == "XTH": 
			dataTH = parsingXiaomi(dataPre[dataItem]["rawData"])
			dataAll["TExterna"] = dataTH["temperature"]
			dataAll["HExterna"] = dataTH["humidity"]
		if interestData[dataItem]["pre"] == "E8C": 
			dataAll["CD"] = 1
		if interestData[dataItem]["pre"] == "E8A": 
			dataAll["AC"] = 1
	return dataAll 

# Parsing Xiaomi TH
def parsingXiaomi(rawData):
	dataParsed = {}
	dataParsed["temperature"] = float(int(rawData[20:24], base=16))/10.0
	dataParsed["humidity"] = float(int(rawData[24:26], base=16))
	return dataParsed

def getSeq():
	seqFile = "/var/www/html/secuence.dat"
	if os.path.exists(seqFile):
		f = open(seqFile, "r")
		try:
			seqNumber = int(f.readline())
		except:
			seqNumber = 0
		f.close()
	else:
		seqNumber = 0
	seqNumberNext = seqNumber + 1
	if seqNumber == 999:
		seqNumberNext = 0 
	f = open(seqFile, "w")
	f.write('%03d' % (seqNumberNext))
	return ('%03d' % seqNumber)

# Envia data a aprs
def send2aprs(dataTelemetry):
	
	seqStr = getSeq()
	seqNum = int(seqStr)
	
	# APRS-IS login info
	serverHost = "noam.aprs2.net"
	serverPort = 14580
	aprsUser = "<YOUR CALLSIGN>"
	aprsSSID = "<MODIFIER>"
	aprsPass = "<YOUR PASS>"
	aprsLongitude = "<YOUR LONGITUDE>"
	aprsLatitude = "<YOUR LATITUDE>"
	symbol = "-"
	comment = "<YOUR COMMENTS>"
	secuenceFile = "secuence.dat"

	# Get current time and date
	dateTimeObj = datetime.now()
	aprsTime = dateTimeObj.strftime("%H%M%S")

	# Get current secuence or create if not exist

	# create socket & connect to server
	sSock = socket(AF_INET, SOCK_STREAM)
	sSock.connect((serverHost, serverPort))
	aprsUser = aprsUser + "-" + aprsSSID
	# logon
	logonString = "user " + aprsUser + " pass " + aprsPass + " vers KD7LXL-Python 0.1\n"
	sSock.sendall(logonString.encode("utf-8"))

	if (seqNum % 5 == 0):
		# send position packet
		# APRS,TCPIP*,qAC,T2BC:@092514z0745.97N/07213.74W?CPU: 11.7%Temp: 45.5C
		payload = "@" + aprsTime + "z" + aprsLongitude + "/" + aprsLatitude + symbol + comment
		packetString = aprsUser + ">APRS,TCPIP*:" + payload + "\n"
		sSock.sendall(packetString.encode("utf-8"))

		# send telemetry config packet 
		# 2022-11-03 08:11:38 -05: W6BSD-5>APDW16,TCPIP*,qAC,T2ALBERTA::W6BSD-5  :PARM.TempExterna,HumExterna,TempInterna,HumInterna
		payload = ":" + aprsUser + " :PARM.TempExterna,HumExterna,TempInterna,HumInterna,,AC,CD,NC,MC"
		packetString = aprsUser + ">APRS,TCPIP*:" + payload + "\n"
		sSock.sendall(packetString.encode("utf-8"))

		# 2022-11-03 08:11:41 -05: W6BSD-5>APDW16,TCPIP*,qAC,T2ALBERTA::W6BSD-5  :UNIT.C,%,C,%
		payload = ":" + aprsUser + " :UNIT.C,%,C,%"
		packetString = aprsUser + ">APRS,TCPIP*:" + payload + "\n"
		sSock.sendall(packetString.encode("utf-8"))

		# 2022-11-03 08:11:42 -05: W6BSD-5>APDW16,TCPIP*,qAC,T2ALBERTA::W6BSD-5  :EQNS.0,0.1,0,0,0.1,0,0,0.1,0,0,0.1,0
		payload = ":" + aprsUser + " :EQNS.0,0.1,0,0,0.1,0,0,0.1,0,0,0.1,0,"
		packetString = aprsUser + ">APRS,TCPIP*:" + payload + "\n"
		sSock.sendall(packetString.encode("utf-8"))

	# send telemetry packet 
	# 2022-11-03 08:11:45 -05: W6BSD-5>APDW16,TCPIP*,qAC,T2ALBERTA:T#000,234,679,251,819,0,00000000
	payload = "T#" + seqStr + ","
	payload = payload + str(int(dataTelemetry["TExterna"]*10)) + ","
	payload = payload + str(int(dataTelemetry["HExterna"]*10)) + ","
	payload = payload + str(int(dataTelemetry["TInterna"]*10)) + ","
	payload = payload + str(int(dataTelemetry["HInterna"]*10)) + ",,"
	payload = payload + str(int(dataTelemetry["AC"])) + str(int(dataTelemetry["CD"])) + "000000"
	packetString = aprsUser + ">APRS,TCPIP*:" + payload + "\n"
	sSock.sendall(packetString.encode("utf-8"))

	# close socket
	sSock.shutdown(0)
	
	'''
	AIS = aprslib.IS("HJ2ALF", passwd="17839", port=14580)
	#AIS = aprslib.IS("YY2ALF", passwd="21692", port=14580)
	dateTimeObj = datetime.now()
	aprsTime = dateTimeObj.strftime("%H%M%S")
	AIS.connect()
	dataTelemetry = "TempExt:"+str(dataTelemetry["TExterna"])+"C HumExt:"+str(dataTelemetry["HExterna"])+"% TempInt:"+str(dataTelemetry["TInterna"])+"C HumInt:"+str(dataTelemetry["HInterna"])+"%"
	AIS.sendall('HJ2ALF>APRS,TCPIP*:@'+ aprsTime + 'h' + '0615.52N/07535.63W' + "-" + dataTelemetry)
	'''
	return 

def application(environment, start_response):
	status = '200 OK'
	response_headers = [('Content-type', 'text/plain')]
	start_response(status, response_headers)
	output = b'Fail: need post request with json data.\n'
	if environment['REQUEST_METHOD'] == 'POST':
		output = environment['wsgi.input'].read()
		#f = open('inputbad.json')
		#output = f.readline()
		#f.close()
		#print(output)
		try:
		#if True:
			json_object = json.loads(output)
			dataDevices = extractOnlyInterest(json_object)
			dataTelemetry = parsingData(dataDevices)
			send2aprs(dataTelemetry)
		except:
		#else: 
			output = b'Fail: json format error.\n'
	return [output]

#env = {}
#env["REQUEST_METHOD"]='POST'
#application(env,0)

