import sys
from ofxparse import OfxParser

'''
BEGIN SETTINGS
'''

# Name of sqlite database
SQLITE_DB_NAME = "tb.db"

'''
END SETTINGS
'''

class Account(object):
	def __init__(self):
		self.number = None
		# Put other attributes here

	def __str__(self):
		return "[Account number:{0}]".format(self.number)

'''
BEGIN OFX
'''

class OfxFileDataLoader(object):
	def __init__(self, ofx_file):
		self.ofx_file = ofx_file
		self.ofx_data = None

	def fetch(self):
		'''
		Fetches the ofx_data from given file path (once)
		'''

		if self.ofx_data == None:
			self.ofx_data = OfxParser.parse(file(self.ofx_file))

		return self.ofx_data

class AccountsOfxMapper(object):
	def __init__(self, ofx_data_loader):
		self.ofx_data_loader = ofx_data_loader

	def get_account(self):
		'''
		Maps the OFX Account object
		into a TB Account object
		'''

		account = Account()
		data = self.ofx_data_loader.fetch()

		account.number = data.account.number

		return account

'''
END OFX
'''


def main():
	file_path = sys.argv[1]
	data_loader = OfxFileDataLoader(file_path)
	accounts_mapper = AccountsOfxMapper(data_loader)
	account = accounts_mapper.get_account()

	print account

if __name__ == '__main__':
	main()