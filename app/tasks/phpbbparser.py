import urllib, socket
from bs4 import *
from urllib.parse import urljoin
import urllib.request
import os.path
import time

class Profile:
	def __init__(self, username):
		self.username = username
		self.signature = ""
		self.properties = {}

	def set(self, key, value):
		self.properties[key] = value

	def get(self, key):
		return self.properties[key] if key in self.properties else None

	def __str__(self):
		return self.username + "\n" + str(self.signature) + "\n" + str(self.properties)

def __extract_properties(profile, soup):
	el = soup.find(id="viewprofile")
	if el is None:
		return None

	res = el.find_all("dl", class_ = "left-box details")
	if len(res) != 1:
		return None

	catch_next_key = None

	# Look through
	for element in res[0].children:
		if element.name == "dt":
			if catch_next_key is None:
				catch_next_key = element.text.lower()[:-1].strip()
			else:
				print("Unexpected dt!")

		elif element.name == "dd":
			if catch_next_key is None:
				print("Unexpected dd!")
			else:
				if catch_next_key != "groups":
					profile.set(catch_next_key, element.text)
				catch_next_key = None

		elif element and element.name is not None:
			print("Unexpected other")

def __extract_signature(soup):
	res = soup.find_all("div", class_="signature")
	if (len(res) != 1):
		return None
	else:
		return res[0]

def getProfile(url, username):
	url = url + "/memberlist.php?mode=viewprofile&un=" + username

	contents = urllib.request.urlopen(url).read().decode("utf-8")
	soup = BeautifulSoup(contents, "lxml")
	if soup is None:
		return None
	else:
		profile = Profile(username)
		profile.signature = __extract_signature(soup)
		__extract_properties(profile, soup)

		return profile
