#!/usr/bin/python3
import urllib.request,json,math

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

#class LinesDB:
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
			if stopToFind in stop['name']:
				stopObj=Stop(stop['shortName'],stop['id'],stop['name'],stop['latitude']/3600000.0,stop['longitude']/3600000.0)
				matchingStops.append(stopObj)
		return matchingStops
class Stop:
	ident=""
	name=""
	latitude=0.0
	longitude=0.0
	shortName=""
	lines=[]

	def __str__(self):
		return "Tram/Bus Stop Name='"+self.name+"' ["+self.shortName+"] Coords=("+str(self.longitude)+","+str(self.latitude)+")"

	def __init__(self,shortName,ident,name,latitude,longitude):
		self.shortName=shortName
		self.ident=ident
		self.name=name
		self.latitude=latitude
		self.longitude=longitude

		#TODO: get lines

	def isWithinRange(self,otherStop,distance):
		dist=Haversine([self.longitude,self.latitude],[otherStop.longitude,otherStop.latitude])
		return dist.km<=distance/1000


_StopsDB=StopsDB()
banacha=_StopsDB.find("Banacha")[0]
print(banacha)
gnw=_StopsDB.find("Górka Narodowa Wschód")[0]
print(gnw)
cm=_StopsDB.find("Czerwone Maki")[0]
print(cm)
print(banacha.isWithinRange(gnw,1000))
print(banacha.isWithinRange(cm,1000))