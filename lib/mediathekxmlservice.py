# -*- coding: utf-8 -*-
import xbmc
import listing
import urllib
import xbmcaddon

translation = xbmcaddon.Addon(id='script.module.libMediathek').getLocalizedString
params = {}

#http://www.zdf.de/ZDFmediathek
def getNew(baseUrl):
	return listing.getXML(baseUrl+'/xmlservice/web/aktuellste?maxLength=50&id=%5FSTARTSEITE')
def getMostViewed(baseUrl):
	return listing.getXML(baseUrl+'/xmlservice/web/meistGesehen?maxLength=50&id=%5FGLOBAL')
def getRubrics(baseUrl):
	return listing.getXML(baseUrl+'/xmlservice/web/rubriken')
def getTopics(baseUrl):
	return listing.getXML(baseUrl+'/xmlservice/web/themen')
def getAZ(baseUrl,letter):
	list = listing.getXML(baseUrl+'/xmlservice/web/sendungenAbisZ?characterRangeEnd='+letter+'&detailLevel=2&characterRangeStart='+letter)
	if letter.lower() == "d":
		l = []
		for dict in list:
			name = dict["name"].lower()
			if name.startswith("der ") or name.startswith("die ") or name.startswith("das "):
				if name[4] == 'd':
					l.append(dict)
			else:
				l.append(dict)
		list = l
	return list
def getSearch(baseUrl,search_string):
	return listing.getXML(baseUrl+'/xmlservice/web/detailsSuche?maxLength=50&types=Video&properties=HD%2CUntertitel%2CRSS&searchString='+urllib.quote_plus(search_string))
	
def getXML(url,type=False):
	return listing.getXML(url,type)

def getVideoUrl(url):
	import play
	video,subUrl,offset = play.getVideoUrl(url)
	return video,subUrl,offset
def getSubtitle(subUrl,offset):
	import subtitle
	return subtitle.getSub(subUrl,offset)
