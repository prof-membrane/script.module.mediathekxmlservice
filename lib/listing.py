#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sys
import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import urllib
import _utils as utils
import fanart

showSubtitles = xbmcaddon.Addon().getSetting('subtitle') == 'true'
baseZdf = "http://www.zdf.de/ZDFmediathek"
fallbackImage = "http://www.zdf.de/ZDFmediathek/img/fallback/946x532.jpg"
defaultThumb = ''

shortNextPages = [
	'http://www.zdf.de/ZDFmediathek/xmlservice/web/aktuellste?maxLength=50&id=%5FSTARTSEITE',
	'http://www.zdf.de/ZDFmediathek/xmlservice/web/meistGesehen?maxLength=50&id=%5FGLOBAL']
def getXML(url,forcedType=False):
	baseUrl = url.split('/xmlservice')[0]
	nextPageUrl = url
	#page = int(page)
	#if page > 1:
	#	url += '&offset='+str((page-1)*50)
	
	list = []
	response = utils.getUrl(url)
	
	if not '<teasers>' in response:
		return list
	teasers=re.compile('<teasers>(.+?)</teasers>', re.DOTALL).findall(response)[0]
	match_teaser=re.compile('<teaser(.+?)</teaser>', re.DOTALL).findall(teasers)
	for teaser in match_teaser:
		dict = {}
		#match_member=re.compile('member="(.+?)"', re.DOTALL).findall(teaser)
		type = re.compile('<type>(.+?)</type>', re.DOTALL).findall(teaser)[0]
		if type == 'video':
			dict['thumb'] = chooseThumb(re.compile('<teaserimages>(.+?)</teaserimages>', re.DOTALL).findall(teaser)[0])
		else:
			dict['thumb'] = chooseThumb(re.compile('<teaserimages>(.+?)</teaserimages>', re.DOTALL).findall(teaser)[0],-1)
		dict.update(getInfo(re.compile('<information>(.+?)</information>', re.DOTALL).findall(teaser)[0]))
		dict.update(getDetails(re.compile('<details>(.+?)</details>', re.DOTALL).findall(teaser)[0]))
		#title = cleanTitle(title)
		if type == 'sendung' and dict['duration'] != '0':
			dict['url'] = baseUrl+'/xmlservice/web/aktuellste?maxLength=50&id=' + dict['assetId']
			dict['fanart'] = dict['thumb']
			dict['mode'] ='xmlListPage'
			dict['type'] = 'shows'
			list.append(dict)
		elif type == 'video':
			#dict['plot'] += '\n\n'+dict['airtime'].split(' ')[0]+' | '+toMin(dict['duration'])+' | '+dict['channel']
			if showSubtitles and dict['hasCaption'] == 'true':
				dict['plot'] += '\n\nUntertitel vorhanden'
			dict['url'] = baseUrl+'/xmlservice/web/beitragsDetails?id=' + dict['assetId']
			dict['mode'] = 'xmlPlay'
			if forcedType:
				dict['type'] = forcedType
			else:
				dict['type'] = 'video'
			f = fanart.getFanart(dict['originChannelId'])
			HH,MM = dict['airtime'].split(' ')[-1].split(':')
			dict['time'] = int(HH)*60 + int(MM)
			if f:
				dict['fanart'] = f
			list.append(dict)
		elif type == 'rubrik' or type == 'thema':
			dict['url'] = baseUrl+'/xmlservice/web/aktuellste?maxLength=50&id=' + dict['assetId']
			dict['mode'] = 'xmlListPage'
			dict['type'] = 'dir'
			list.append(dict)
		else:
			xbmc.log('libZdf: unsupported item type "' + type + '"')
	
	nextPageUrl = _checkIfNextPageExists(url,response)
	if nextPageUrl:
		dict = {}
		dict['url'] = nextPageUrl
		dict['type'] = 'nextPage'
		dict['mode'] = 'xmlListPage'
		list.append(dict)
	
	return list
	
def _checkIfNextPageExists(url,response):
	offset = 0
	if '&offset=' in url:
		offset = url.split('&offset=')[-1]
		if '&' in offset:
			offset = offset.split('&')[0]
		url = url.replace('&offset='+offset,'')
		offset = int(offset)
		
	nextPage = False	
	if '<additionalTeaser>' in response:
		nextPage=re.compile('<additionalTeaser>(.+?)</additionalTeaser>', re.DOTALL).findall(response)[0] == 'true'
	elif '<batch>' in response:
		batch=re.compile('<batch>(.+?)</batch>', re.DOTALL).findall(response)[0]
		if int(batch) > offset:
			nextPage = True
	if nextPage:
		return url + '&offset=' + str(offset + 50)
	else:
		return False
	"""
	nextPage = False
	if '<additionalTeaser>' in response:
		nextPage=re.compile('<additionalTeaser>(.+?)</additionalTeaser>', re.DOTALL).findall(response)[0] == 'true'
	elif '<batch>' in response:
		batch=re.compile('<batch>(.+?)</batch>', re.DOTALL).findall(response)[0]
		if int(batch) > page * 50:
			nextPage = True		
			
	if url in shortNextPages and page >= 3:
		nextPage = False
		
	if nextPage:
		return url
	else:
		return False
	"""

def getInfo(infos):
	dict = {}
	dict['name']=re.compile('<title>(.+?)</title>', re.DOTALL).findall(infos)[0].replace('<![CDATA[','').replace(']]>','')
	if '(' in dict['name']:
		s = dict['name'].split('(')
		for possibleEpisode in s:
			possibleEpisode = possibleEpisode.split(')')[0].replace(' ','')
			if '.Teil' in possibleEpisode:
				dict['episode'] = possibleEpisode.replace('.Teil','')
			elif '-' in possibleEpisode:
				if possibleEpisode.split('-')[0].isdigit() and possibleEpisode.split('-')[1].isdigit():
					dict['episode'] = possibleEpisode.split('-')[0]
					dict['season'] = possibleEpisode.split('-')[1]
			elif possibleEpisode.isdigit():
				dict['episode'] = possibleEpisode
	if not 'episode' in dict and 'Teil' in dict['name']:
		possibleEpisode = dict['name'].split('Teil ')[-1].replace('.','')
		if possibleEpisode.isdigit():
			dict['episode'] = possibleEpisode
	try:
		dict['plot']=re.compile('<detail>(.+?)</detail>', re.DOTALL).findall(infos)[0].replace('<![CDATA[','').replace(']]>','')
	except: pass
		
	return dict
	
def chooseThumb(images,maxW=476):
	thumb = fallbackImage
	height = 0
	width = 0
	match_images=re.compile('<teaserimage.+?key="(.+?)x(.+?)">(.+?)</teaserimage>', re.DOTALL).findall(images)
	for w,h,image in match_images:
		if not "fallback" in image:
			if int(h) > height or int(w) > width:
				if maxW == -1 or int(w) <= maxW:
					height = int(h)
					width = int(w)
					thumb = image
	return thumb

def getDetails(details):
	dict = {}
	try:
		dict['assetId']=re.compile('<assetId>(.+?)</assetId>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['originChannelId']=re.compile('<originChannelId>(.+?)</originChannelId>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['tvshowtitle']=re.compile('<originChannelTitle>(.+?)</originChannelTitle>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['channel']=re.compile('<channel>(.+?)</channel>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['channelLogo']=re.compile('<channelLogoSmall>(.+?)</channelLogoSmall>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['airtime']=re.compile('<airtime>(.+?)</airtime>', re.DOTALL).findall(details)[0]
		s = dict['airtime'].split(' ')[0].split('.')
		dict['aired'] = s[2] + '-' + s[1] + '-' + s[0] 
		dict['airedtime'] = dict['airtime'].split(' ')[1]
	except: pass
	try:
		dict['timetolive']=re.compile('<timetolive>(.+?)</timetolive>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['fsk']=re.compile('<fsk>(.+?)</fsk>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['hasCaption']=re.compile('<hasCaption>(.+?)</hasCaption>', re.DOTALL).findall(details)[0]
	except: pass
	try:
		dict['url']=re.compile('<vcmsUrl>(.+?)</vcmsUrl>', re.DOTALL).findall(details)[0]
	except: pass
		
	try:
		if '<lengthSec>' in details:
			dict['duration'] = int(re.compile('<lengthSec>(.+?)</lengthSec>', re.DOTALL).findall(details)[0])
		elif '<length></length>' in details:
			dict['duration'] = 0
		else:
			length=re.compile('<length>(.+?)</length>', re.DOTALL).findall(details)[0]
			if ' min ' in length:
				l = length.split(' min ')
				length = int(l[0]) * 60 + int(l[1])
			elif ' min' in length:
				l = length.replace(' min','')
				length = int(l) * 60
			elif '.000' in length:#get seconds
				length = length.replace('.000','')
				l = length.split(':')
				length = int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])
			dict['duration'] = length
	except: pass
	
	return dict
	
def toMin(s):
	m, s= divmod(int(s), 60)
	M = str(m)
	S = str(s)
	if len(M) == 1:
		M = '0'+M
	if len(S) == 0:
		S = '00'
	elif len(S) == 1:
		S = '0'+S
	return M+':'+S+' Min.'