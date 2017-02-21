#!/usr/bin/python
# -*- coding: utf-8 -*-

# import requests
import json
import sys
from collections import OrderedDict
from bs4 import BeautifulSoup
from datetime import date

replacements = {u' ': u'_',
				u'(': u'_',
				u')': u'',
				u'/': u'_ou_',
				u'-': u'_',
				u'ç': u'c',
				u'á': u'a',
				u'à': u'a',
				u'â': u'a',
				u'ã': u'a',
				u'é': u'e',
				u'ê': u'e',
				u'í': u'i',
				u'ó': u'o',
				u'ú': u'u'}

def format_nicely(u_string):
	u_string = u_string.strip(': ').lower()
	for key in replacements:
		u_string = u_string.replace(key, replacements[key])
	return u_string

def check_cpf(key, first_cpf):
	if key == 'cpf_ou_cgc':
		if first_cpf:
			key = key + '_prop'
			first_cpf = False
		else:
			key = key + '_oper'
			first_cpf = True
	return key, first_cpf

def check_date(key, text):
	if 'data' in key:
		if '/' in text:
			day, month, year = [int(s) for s in text.split('/')]
		else:
			day, month, year = [int(text[0:2]), int(text[2:4]), int(text[4:6])]
		if year < 50:
			year += 2000
		elif year < 1900:
			year += 1900
			
		d = date(year, month, day)
		return d.isoformat()
	else:
		return text

KEY = 0
VALUE = 1

res_f = open(sys.argv[1], 'w+')
html_soup = BeautifulSoup(open(sys.argv[2], 'r'), 'html.parser', from_encoding='utf-8')

state = VALUE
is_header = True
first_cpf = True
plane = OrderedDict({'matricula': 'PRSOM'})

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

res_f.write(json.dumps(plane, indent=4).encode('utf-8') + '\n')
res_f.close()