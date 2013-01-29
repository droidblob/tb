from sqlalchemy import create_engine
from sqlalchemy import Column, Date, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from ofxparse import OfxParser
from decimal import Decimal as D

import sqlalchemy.types as types
import sys

engine = create_engine('sqlite:///tb.db', echo=True)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

####################
class SqliteNumeric(types.TypeDecorator):
    impl = types.String
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))
    def process_bind_param(self, value, dialect):
        return str(value)
    def process_result_value(self, value, dialect):
        return D(value)

Numeric = SqliteNumeric
####################
class Account(Base):
	"""Physical financial account"""

	__tablename__ = "accounts"

	id = Column(Integer, primary_key=True)
	number = Column(String, unique=True, nullable = False)
	balance = Column(Numeric, nullable = False)
	balance_date = Column(Date, nullable = False)

	def __init__(self, number, balance, balance_date):
		self.number = number
		self.balance = balance
		self.balance_date = balance_date
####################
class Transaction(Base):
	"""Physical financial transactions"""

	__tablename__ = "transactions"

	id = Column(Integer, primary_key = True)
	account_id = Column(Integer, ForeignKey('accounts.id'))
	payee = Column(String, nullable = False)
	type = Column(String, nullable = False)
	date = Column(Date, nullable = False)
	amount = Column(Numeric, nullable = False)
	foreign_id = Column(String, nullable = False, unique = True)
	memo = Column(String, nullable = False)

	account = relationship("Account", backref=backref('transactions', order_by=id))

	def __init__(self, payee, type, date, amount, foreign_id, memo):
		self.payee = payee
		self.type = type
		self.date = date
		self.amount = amount
		self.foreign_id = foreign_id
		self.memo = memo
####################


def main():
	Base.metadata.create_all(engine)

	file_path = sys.argv[1]

	# Expensive statement...
	ofx = OfxParser.parse(file(file_path))

	account = Account(ofx.account.number, 
		ofx.account.statement.balance,
		ofx.account.statement.end_date)

	existing_account = session.query(Account).filter_by(number=account.number).first()
	if existing_account:
		account.id = existing_account.id

	# Bulk insert...
	transactions = []
	for ofx_transaction in ofx.account.statement.transactions:
		transactions.insert(0,
			{
				'account_id': account.id,
				'payee': ofx_transaction.payee,
				'type': ofx_transaction.type,
				'date': ofx_transaction.date,
				'amount': ofx_transaction.amount,
				'foreign_id': ofx_transaction.id,
				'memo': ofx_transaction.memo
			}
		)
	session.execute(
		Transaction.__table__.insert().prefix_with("OR IGNORE"),
		transactions
	)

	# IN ORDER TO SUPPORT COMPLETE UPDATES OF TRANSACTIONS
	# TODO
	# 1. Load all transactions into temp table
	# 2. Delete all transactions from real table not in temp table
	# 3. Insert or ignore all transactions into real table from temp
	# 4. Update all transactions into real table from temp
	# 5. Drop temp table

	session.merge(account)
	session.commit()
	
if __name__ == '__main__':
	main()

"""
TODO:
 	- User account: Login/Logout/Register/Forgot Password
 	- OFX upload form
 	- Physical accounts
 	- Physical transactions
 	- Virtual accounts
 		-- Inbox
 		-- Other accounts
 	-- Virtual transctions
 		-- Transfers
 		-- Splits
 	-- Reporting
 		-- (Look around for these)
 	-- Planning
 		-- Scheduled (one-time/repeating) transactions
 		-- Cashflow/balance forecast
 			-- Projected vs actual
"""