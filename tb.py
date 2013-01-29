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
		self.balance = None
		# Put other attributes here

	def __str__(self):
		return "[Account number:{0}, balance:{1}]".format(self.number, self.balance)

class Transaction(object):
	"""Financial transaction object"""
	def __init__(self):
		self.payee = None
		self.type = None
		self.date = None
		self.amount = None
		self.foreign_id = None
		self.memo = None

	def __str__(self):
		return "[Transaction payee: {0}, type: {1}, date: {2}, amount: {3}]".format(self.payee, self.type, self.date, self.amount)

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
		account.balance = data.account.statement.balance
		# Put other attribute mappings here

		return account

class TransactionsOfxMapper(object):
	def __init__(self, ofx_data_loader):
		self.ofx_data_loader = ofx_data_loader

	def get_transactions(self):
		'''
		Maps the OFX Transactions list
		into a TB Transactions list
		'''

		transactions = []
		data = self.ofx_data_loader.fetch()

		for ofx_transaction in data.account.statement.transactions:
			transaction = Transaction()
			transaction.payee = ofx_transaction.payee
			transaction.type = ofx_transaction.type
			transaction.date = ofx_transaction.date
			transaction.amount = ofx_transaction.amount
			transaction.foreign_id = ofx_transaction.id
			transaction.memo = ofx_transaction.memo

			transactions.insert(0, transaction)
			# Put other attribute mappings here

		return transactions

'''
END OFX
'''


def main():
	file_path = sys.argv[1]
	data_loader = OfxFileDataLoader(file_path)
	accounts_mapper = AccountsOfxMapper(data_loader)
	account = accounts_mapper.get_account()

	transactions_mapper = TransactionsOfxMapper(data_loader)
	transactions = transactions_mapper.get_transactions()

	print account
	print transactions[0]

if __name__ == '__main__':
	main()