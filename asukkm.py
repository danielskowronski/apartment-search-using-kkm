#!/usr/bin/python3
import urllib.request,json,math,base64,re,argparse
from pprint import pprint

class Haversine:
	#SOURCE: https://nathanrooy.github.io/posts/2016-09-07/haversine-with-python/
    def __init__(self,coord1,coord2):
        lon1,lat1=coord1
        lon2,lat2=coord2
        
        R=6371000                               # radius of Earth in meters
        phi_1=math.radians(lat1)
        phi_2=math.radians(lat2)

        delta_phi=math.radians(lat2-lat1)
        delta_lambda=math.radians(lon2-lon1)

        a=math.sin(delta_phi/2.0)**2+\
           math.cos(phi_1)*math.cos(phi_2)*\
           math.sin(delta_lambda/2.0)**2
        c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))
        
        self.meters=R*c                         # output distance in meters
        self.km=self.meters/1000.0              # output distance in kilometers
        self.miles=self.meters*0.000621371      # output distance in miles
        self.feet=self.miles*5280               # output distance in feet

class LinesDB:
	apiServer="http://rozklady.mpk.krakow.pl/?lang=PL&"
	stopsByLine=dict()
	linesByStop=dict()

	def __APIrequest(self,url):
		req = urllib.request.Request(
    		self.apiServer+url, 
			data=None, 
			headers={
				'Cookie': 'ROZKLADY_JEZYK=PL; ROZKLADY_WIDTH=2000; ROZKLADY_AB=0; ROZKLADY_WIZYTA=0; ROZKLADY_OSTATNIA=0'
			}
		)
		f = urllib.request.urlopen(req)
		return f.read().decode('utf-8')

	def fixWeirdBase64(self,txt):
		return txt+ "=" * ((4 - len(txt) % 4) % 4)

	def fetchStopsAtLine(self,line):
		data=self.__APIrequest("linia="+line)
		m=re.findall("przystanek=(.*)'",data)
		stopIDs=list(set(m))
		stops=list()
		for stopID in stopIDs:
			fixed=self.fixWeirdBase64(stopID)
			decoded=base64.b64decode(fixed).decode('utf-8',errors='ignore')
			stopInstances=_StopsDB.find(decoded)
			for stop in stopInstances:
				stops.append(stop)
		return stops
	def getStopsAtLine(self,line):
		if not line in self.stopsByLine:
			self.stopsByLine[line]=self.fetchStopsAtLine(line)
		return self.stopsByLine[line]

	def fetchLinesAtStop(self,stop):
		stopID=base64.encodebytes(stop.name.encode()).decode().replace("=","")
		data=self.__APIrequest("akcja=przystanek&przystanek="+stopID)
		m=re.findall("linia=(\d+)__",data)
		lines=list(set(m))
		return lines
	def getLinesAtStop(self,stop):
		if not stop.shortName in self.linesByStop:
			self.linesByStop[stop.shortName]=self.fetchLinesAtStop(stop)
		return self.linesByStop[stop.shortName]

	#def __init__(self):
	#	
class StopsDB:
	apiServers=["http://www.ttss.krakow.pl","http://91.223.13.70"]
	apiPath="/internetservice/geoserviceDispatcher/services/stopinfo/stops?left=-648000000&bottom=-324000000&right=648000000&top=324000000"
	allStops=[]

	def __init__(self):
		for apiServer in self.apiServers:
			stops=json.loads(urllib.request.urlopen(apiServer+self.apiPath).read())
			for stop in stops['stops']:
				self.allStops.append(stop)
		print("StopsDB: Found "+str(len(self.allStops))+" stops")
	def find(self,stopToFind):
		matchingStops=[]
		for stop in self.allStops:
			if stopToFind in stop['name'] or stop['name'] in stopToFind:
				stopObj=Stop(stop['shortName'],stop['id'],stop['name'],stop['latitude']/3600000.0,stop['longitude']/3600000.0)
				matchingStops.append(stopObj)
		return matchingStops
	def constructByShortname(self,shortname):
		for stop in self.allStops:
			if stop['shortName']==shortname:
				stopObj=Stop(stop['shortName'],stop['id'],stop['name'],stop['latitude']/3600000.0,stop['longitude']/3600000.0)
				return stopObj
		return None
class Stop:
	ident=""
	name=""
	latitude=0.0
	longitude=0.0
	shortName=""

	def __str__(self):
		return "Tram/Bus Stop Name='"+self.name+"' ["+self.shortName+"] Coords=("+str(self.longitude)+","+str(self.latitude)+")"

	def __init__(self,shortName,ident,name,latitude,longitude):
		self.shortName=shortName
		self.ident=ident
		self.name=name
		self.latitude=latitude
		self.longitude=longitude

	def isWithinRange(self,otherStop,distance):
		dist=Haversine([self.longitude,self.latitude],[otherStop.longitude,otherStop.latitude])
		return dist.km<=distance/1000

def debugPrint(txt):
	if verboseLevel>0:
		print("~~debug: "+txt)

parser = argparse.ArgumentParser(description="apartment-search-using-kkm")
parser.add_argument("stop",type=str,nargs=2,help="tram/bus stop base name")
parser.add_argument("distance",type=int,nargs=1,help="max distance in meters")
parser.add_argument("--verbose","-v",action="count")
args = parser.parse_args()

verboseLevel=args.verbose
distance=args.distance[0]

_StopsDB=StopsDB()
stop1=_StopsDB.find(args.stop[0])[0]
stop2=_StopsDB.find(args.stop[1])[0]

_LinesDB=LinesDB()
linesToConsider1=_LinesDB.getLinesAtStop(stop1)
linesToConsider2=_LinesDB.getLinesAtStop(stop2)

def checkOrSkip(line):
	if line[0]=="9" or line[0]=="6":
		debugPrint("Skipping night line: "+line)
		return False
	if line[0]=="7":
		debugPrint("Skipping temporary line: "+line)
		return False
	debugPrint("Will consider line: "+line)
	return True

print("LinesDB: Fetching lines for "+str(stop1))
for line in linesToConsider1:
	if not checkOrSkip(line):
		continue
	stopsForConnection1=_LinesDB.getStopsAtLine(line)
print("LinesDB: Fetching lines for "+str(stop2))
for line in linesToConsider2:
	if not checkOrSkip(line):
		continue
	stopsForConnection2=_LinesDB.getStopsAtLine(line)

matchingShortNamesStopsMatrix=[]
for stopA in stopsForConnection1:
	for stopB in stopsForConnection2:
		if stopA.isWithinRange(stopB,distance):
			matchingShortNamesStopsMatrix.append((stopA.shortName,stopB.shortName))
uniqueMatchingStopsMatrix=list(set(matchingShortNamesStopsMatrix))

i=0
for pair in uniqueMatchingStopsMatrix:
	i+=1
	stopA=_StopsDB.constructByShortname(pair[0])
	stopB=_StopsDB.constructByShortname(pair[1])
	print("Matching stops #"+str(i).zfill(4)+": "+stopA.name+", "+stopB.name)
print(" ASUKKM: Found "+str(i)+" matching stops")