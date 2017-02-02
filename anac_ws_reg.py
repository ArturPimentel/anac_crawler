import requests
import json
from bs4 import BeautifulSoup
from string import ascii_uppercase

# Makes a list of all possible Brazillian registrations
def make_prefix_list():
	prefix_list = ["PP", "PT", "PR", "PU"]
	registrations = []

	for prefix in prefix_list:
		for letter_1 in ascii_uppercase:
			for letter_2 in ascii_uppercase:
				for letter_3 in ascii_uppercase:
					suffix = letter_1 + letter_2 + letter_3
					registrations.append(prefix + suffix)

	return registrations

###############################################################################
res_f = open(str(datetime.date.today()) + ".json", "w")
url = "https://sistemas.anac.gov.br/aeronaves/cons_rab.asp"
registrations = make_prefix_list()

# Request every registration possible
for i, registration  in enumerate(registrations):
	html = requests.post(
		url,
		data={'radiobutton': 'p',
			  'txmtc': registration,
			  'enviar': 'ok'},
		verify=False # ANAC site has not updated certificate
	).text
	
	# If registration exists, parse HTML and look for info
	if 'MATR' in html:
		print registration
		html_soup = BeautifulSoup(html, 'html.parser')
		is_cpf = True
		plane = {u'Matr\xedcula': registration}

		# Relevant info is marked with 'tx_bd' class
		for line in html_soup.find_all("td", class_="tx_bd"):
			if line.div != None:
				# Attribute name is inside 'div' and 'span' tags
				if line.div.span != None:
					if line.div.span.string != None:
						key = line.div.span.string.strip(":")
						# In the webpage there are two places that read 'CPF/CGC'
						if key == 'CPF/CGC':
							if is_cpf:
								key = key + '(Prop)'
								is_cpf = False
							else:
								key = key + '(Oper)'
								is_cpf = True

				# Attribute value is only inside 'div' tags, just after a attribute name
				elif line.div.string != None:
					plane[key] = line.div.string

		# Save info into a json
		res_f.write(str(json.dumps(plane)).encode('utf-8') + '\n')

res_f.close()