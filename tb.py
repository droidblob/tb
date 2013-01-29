import sys
import sqlite3


from decimal import Decimal
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
		self.balance_date = None
		# Put other attributes here

	def __str__(self):
		return "[Account number:{0}, balance:{1}, balance_date:{2}]".format(self.number, self.balance, self.balance_date)

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
BEGIN Sql
'''

def sqlite_adapt_decimal(d):
	return str(d)

def sqlite_convert_decimal(s):
	return Decimal(s)

class DBConnectionManager(object):
	def __init__(self):
		sqlite3.register_adapter(Decimal, sqlite_adapt_decimal)
		sqlite3.register_converter("decimal", sqlite_convert_decimal)

	def get_connection(self):
		# May need to be more intelligent about this
		return sqlite3.connect(SQLITE_DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)


class AccountSqliteAccess(object):
	"""Class to access sqlite-backed accounts"""

	DDL_ACCOUNT_CREATE = """
	CREATE TABLE IF NOT EXISTS
	accounts
	(
		id INTEGER NOT NULL,
		number TEXT NOT NULL,
		balance DECIMAL NOT NULL,
		balance_date TIMESTAMP NOT NULL,
		PRIMARY KEY (id),
		UNIQUE (number)
	)
	"""

	DML_ACCOUNT_INSERT = """
	INSERT OR IGNORE INTO accounts
	(
		number, balance, balance_date
	)
	VALUES
	(
		:number, :balance, :balance_date
	)
	"""

	DML_ACCOUNT_UPDATE = """
	UPDATE accounts
	SET
		balance = :balance,
		balance_date = :balance_date
	WHERE
		number = :number
	"""

	def __init__(self, db):
		self.db = db

	def _setup_table(self, db_connection):
		with db_connection:
			c = db_connection.cursor()
			c.execute(self.DDL_ACCOUNT_CREATE)
			
	
	def insert(self, account):
		con = self.db.get_connection()
		try:
			with con:
				self._setup_table(con)
				c = con.cursor()
				c.execute(self.DML_ACCOUNT_INSERT, {
					'number': account.number,
					'balance': account.balance,
					'balance_date': account.balance_date
					})
				rowcount = c.rowcount

		finally:
			con.close()

		return rowcount

	def update(self, account):
		con = self.db.get_connection()
		try:
			with con:
				self._setup_table(con)
				c = con.cursor()
				c.execute(self.DML_ACCOUNT_UPDATE, {
					'number': account.number,
					'balance': account.balance,
					'balance_date': account.balance_date
					})

				rowcount = c.rowcount
		finally:
			con.close()

		return rowcount


'''
END Sql
'''

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
		account.balance_date = data.account.statement.end_date
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

	db_conn = DBConnectionManager()
	accounts_db = AccountSqliteAccess(db_conn)

	rows = 0
	updated_rows = 0

	rows = accounts_db.insert(account)

	if rows <= 0:
		updated_rows = accounts_db.update(account)

	print account
	print transactions[0]
	print "Insert rows affected: ", rows
	print "Update rows affected: ", updated_rows

if __name__ == '__main__':
	main()