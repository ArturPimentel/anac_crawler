#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import sys

from datetime import date
from collections import OrderedDict
from bs4 import BeautifulSoup
from string import ascii_uppercase

#####################################CONSTANTS#################################
# States for our scraping
KEY = 0
VALUE = 1


######################################FUNCTIONS################################
# Checks whether a value represnts an integer
def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

# Normalizes a PT-BR string
def format_nicely(string):
	replacements = {u' ': u'_', u'(': u'_', u')': u'', u'/': u'_ou_',
					u'-': u'_', u'ç': u'c', u'á': u'a', u'à': u'a', u'â': u'a',
					u'ã': u'a', u'é': u'e', u'ê': u'e', u'í': u'i', u'ó': u'o',
					u'ú': u'u'}
	
	string = string.strip(': ').lower()
	for key in replacements:
		string = string.replace(key, replacements[key])
	return string

# Checks whether a key represents a CPF and if it is one, determines wheter is 
# an owner CPF or a operator CPF
def check_cpf(key, first_cpf):
	if key == 'cpf_ou_cgc':
		if first_cpf:
			key = key + '_prop'
			first_cpf = False
		else:
			key = key + '_oper'
			first_cpf = True
	return key, first_cpf

# Checks whether a value represents a date and return that date in ISO format
def check_date(key, text):
	if 'data' in key:
		if not represents_int(text[0]):
			return None

		if '/' in text:
			day, month, year = [int(s) for s in text.split('/')]
		else:
			day, month, year = [int(text[0:2]), int(text[2:4]), int(text[4:6])]
		if year < 50: # Most years are represented by just two digits. 50 is arbitrary
			year += 2000
		elif year < 1900:
			year += 1900
			
		d = date(year, month, day)
		return d.isoformat()
	else:
		return text

# Makes a list of all possible Brazillian planes' registrations
def make_prefix_list(last_registration):
	prefix_list = ["PP", "PT", "PR", "PU"]
	registrations = []

	for prefix in prefix_list:
		for letter_1 in ascii_uppercase:
			for letter_2 in ascii_uppercase:
				for letter_3 in ascii_uppercase:
					suffix = letter_1 + letter_2 + letter_3
					registrations.append(prefix + suffix)

	return registrations[registrations.index(last_registration.strip('\n')):]

# Makes a request to ANAC site
# TODO: Should be able to try once more every minute
# TODO: After 3 failed tries, save registration of the last attempt
def make_request(url, data, save_file):
	try:
		# ANAC site does not have an updated certificate
		html = requests.post(url, data=data, verify=False).text
	except ConnetionError, e:
		print "Connection with ANAC site was terminated. Verify internet connection"
		save_last_search.write(data['txmtc'])
		save_last_search.close()
		sys.exit(0)
	return html

# Scraps ANAC site for a given registration
# TODO: fill this function
def scrap_for(registration):
	pass

#######################################MAIN####################################
def main():
	result_file = open(str(date.today()) + ".json", "w+")
	save_file = open("search_save.txt", "r")
	last_registration = save_file.readline()
	save_file.close()
	save_file = open("search_save.txt", "w")
	url = "https://sistemas.anac.gov.br/aeronaves/cons_rab.asp"
	registrations = make_prefix_list(last_registration)

	# Request every registration possible
	for i, registration  in enumerate(registrations):
		html = make_request(
			url,
			{'radiobutton': 'p',
			 'txmtc': registration,
			 'enviar': 'ok'},
			save_file
		)
		
		# If registration exists, parse HTML and look for info
		if 'MATR' in html:
			print registration
			html_soup = BeautifulSoup(html, 'html.parser')
			state = VALUE
			is_header = True
			first_cpf = True
			plane = OrderedDict({'matricula': registration})

			# Relevant info is marked with 'tx_bd' class
			for element in html_soup.find_all('td', class_='tx_bd'):
				text = element.get_text().strip(' \n\t\r')

				if text == u'Proprietário:':
					is_header = False
					state = KEY

				if text != '' and not is_header:
					if ':' in text:
						if state == KEY:
							key = format_nicely(text)
						else: # Value was null
							key, first_cpf = check_cpf(key, first_cpf)
							plane.update({key: None})
							key = format_nicely(text)
						state = VALUE
					else:
						if state == VALUE:
							key, first_cpf = check_cpf(key, first_cpf)
							value = check_date(key, text)
							plane.update({key: value})
							state = KEY

			result_file.write(json.dumps(plane).encode('utf-8') + '\n')
	
	save_file.close()
	result_file.close()

if __name__ == '__main__':
	main()