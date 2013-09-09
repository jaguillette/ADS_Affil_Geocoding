import requests
import json
import csv
import time
import os

#Function to define global CSV writer objects.
def open_global_csv(filename, labelList):
    csvfile=open(filename+'.csv', 'wb+')
    W=csv.writer(csvfile, delimiter=',', quotechar='"')
    #row headers below
    W.writerow(labelList)
    #writes header
    return W

#GLOBAL VARIABLES
BIBCODE_LIST_FILENAME=raw_input('Bibcode list file name: ')

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)
ensure_dir(BIBCODE_LIST_FILENAME)
BIB_PATH=os.path.abspath(BIBCODE_LIST_FILENAME)
ensure_dir(BIB_PATH+"/bibcodes")

ADS_URL_BASE='http://labs.adsabs.harvard.edu/adsabs/api/search/'
ADS_DEV_KEY=open('API_KEY.txt', 'r').read()
GEO_URL_BASE='http://maps.googleapis.com/maps/api/geocode/json'
ERROR_WRITER=open_global_csv(BIB_PATH+'/geoErrors', ['bibcode', 'loc', 'status','count','time'])
#^Opens csv to be used to record bibcodes and locations where the geocoordinates could not be found.
NOAFFIL_WRITER=open_global_csv(BIB_PATH+'/noAffil', ['bibcode'])
#^Opens csv to be used to record bibcodes with no affiliation data.
NOBIB_WRITER=open_global_csv(BIB_PATH+'/noBib', ['bibcode'])
#^Opens csv to be used to record bibcodes that the API could not find a record for.
SET_WRITER=open_global_csv(BIB_PATH+'/geo_affil_set', ['bibcode','Location','lat','long','address','country','state','trusted','count'])
#^Opens csv to be used to record all information for the current set of bibcodes.

#Function takes a bibcode as an argument, returns a dictionary from the json that the ADS API returns.
def adsQuery(bibcode):
	time.sleep(1)
	apiBib='bibcode:'+bibcode
	Q={'dev_key':ADS_DEV_KEY, 'q':apiBib, 'fl':'aff'}
	adsRequest=requests.get(ADS_URL_BASE, params=Q)
	ADSreturndict=adsRequest.json()
	return ADSreturndict

#Cleaner for addresses, splits addresses with semicolons, takes the first affiliation. Also takes out any leading whitespace.
def cleanLocation(loc):
	clean_01=loc.encode('utf-8')
	if ';' in clean_01:
		clean_02=clean_01.split(';')
	else:
		clean_02=[clean_01]
	clean_03=[i.lstrip() for i in clean_02]
	return clean_03

#Makes a list of addresses from the affiliations of the ADS query for one bibcode, sends them to the cleaning function,
#then takes the set of unique affiliations and returns them as a dictionary, 
#such that the affiliation is paired with the number of times it occured in that bibcode.
def getAddrDict(bibcode):
	ads_dict=adsQuery(bibcode)
	cleanAddrList=[]
	addrDict={}
	try:
		addrList=ads_dict['results']['docs'][0]['aff']
		for i in addrList:
			loc=cleanLocation(i)
			for ele in loc:
				cleanAddrList.append(ele)
				uniqueAddrList=list(set(cleanAddrList))
				for i in uniqueAddrList:
					addrDict[i]=cleanAddrList.count(i)
		return addrDict
	except KeyError:
		print "Could not process {0}. Affiliations not recorded.".format(bibcode)
		writeList = [bibcode]
		NOAFFIL_WRITER.writerow(writeList)
		addrList=[]
		return 0
	except IndexError:
		print "Could not process "+bibcode+". The ADS API returned no results."
		writeList = [bibcode]
		NOBIB_WRITER.writerow(writeList)
		addrList=[]
		return 0

#Opens a csv file to write bibcode affiliation geocoding info to, returns a csv writer object.
def open_output_csv(bibcode):
    csvfile=open(BIB_PATH+'/bibcodes/'+bibcode+'.csv', 'wb+')
    W=csv.writer(csvfile, delimiter=',', quotechar='"')
    #row headers below
    W.writerow(['bibcode','Location','lat','long','address','country','state','trusted','count'])
    #writes header
    return W

#Takes a location and the bibcode and count from the address dictionary, and sends it to a Google API for geocoding.
#Responses are written into a list, to be written to later.
#each column to be written to is assigned its own variable, and encoded in utf-8
def geoQuery(loc, bibcode, count):
	Q={'address':loc, 'sensor':'false'}
	geoRequest=requests.get(GEO_URL_BASE, params=Q)
	geoDict=geoRequest.json()
	if geoDict['status'] == 'OK':
		lat=geoDict['results'][0]['geometry']['location']['lat']
		lng=geoDict['results'][0]['geometry']['location']['lng']
		country='NULL'
		state='NULL'
		trusted=False
		for i in geoDict['results'][0]['address_components']:
			if 'country' in i['types']:
				country=i['long_name']
			if 'administrative_area_level_1' in i['types']:
				state=i['long_name']
			if 'route' in i['types']:
				trusted=True
		address=geoDict['results'][0]['formatted_address']
		lat=str(lat).encode('utf-8')
		lng=str(lng).encode('utf-8')
		country=country.encode('utf-8')
		state=state.encode('utf-8')
		address=address.encode('utf-8')
		count=str(count).encode('utf-8')
		bibcode=bibcode.encode('utf-8')
		writeList=[bibcode,loc,lat,lng,address,country,state,trusted,count]
	else:
		writeList=[bibcode, loc, geoDict['status'],count,time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())]
	return writeList

#takes writelist from previous function, as well as writer, determines whether query was successful based on writer length
#Writes to either (error csv) or (set csv and bibcode csv)
def geoQueryWriter(writeList, csvWriter):
	if len(writeList)>=6:
		csvWriter.writerow(writeList)
		SET_WRITER.writerow(writeList)
	elif len(writeList)==5:
		ERROR_WRITER.writerow(writeList)

#container that runs the queries and writers, takes a bibcode to pass all the way down the chain of functions
#also reports status of script via print, makes script wait to reduce timeout errors from Google.
def geoQueryContainer(bibcode):
	csvWriter=open_output_csv(bibcode)
	addrDict=getAddrDict(bibcode)
	try:
		addrLen=str(len(addrDict))
		print "Bibcode: "+bibcode+" has {0} affiliation addresses to process.".format(addrLen)
		for i in addrDict.keys():
			writeList=geoQuery(i,bibcode,addrDict[i])
			time.sleep(1)
			geoQueryWriter(writeList, csvWriter)
		return 0
	except TypeError:
		return 0

#opens bibcode list, one row of a lot of bibcodes.
def openBibCodeList(name):
	csvfile=open("{0}.csv".format(name), 'rb')
	R=csv.reader(csvfile, delimiter=',', quotechar='"')
	return R

#Takes a csv with a list of bibcodes in one row, then tries to get the geocoding for all of them.
def geocodeBibcodeList(listname):
	BibList=[row[0] for row in openBibCodeList(listname)]
	LenBibList=len(BibList)
	counter=1
	for code in BibList:
		geoQueryContainer(code)
		strCounter=str(counter)
		strLenBibList=str(LenBibList)
		print "{0} of {1} bibcodes processed.".format(strCounter, strLenBibList)
		print ""
		counter+=1
	return 0

geocodeBibcodeList(BIBCODE_LIST_FILENAME)