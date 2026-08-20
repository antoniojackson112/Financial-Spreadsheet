from database import init_db, connect

RULES = [
(1,'Yes','WAWA','Food','Dining Out','Expense',0),
(2,'Yes','CHICK-FIL-A','Food','Dining Out','Expense',0),
(3,'Yes','MCDONALD','Food','Dining Out','Expense',0),
(4,'Yes','TARGET','Shopping','General','Expense',0),
(5,'Yes','WALMART','Shopping','General','Expense',0),
(6,'Yes','AMAZON','Shopping','Online Shopping','Expense',0),
(7,'Yes','UBER','Transportation','Rideshare','Expense',0),
(8,'Yes','LYFT','Transportation','Rideshare','Expense',0),
(9,'Yes','SHELL','Transportation','Gas','Expense',0),
(10,'Yes','EXXON','Transportation','Gas','Expense',0),
(11,'Yes','NETFLIX','Subscriptions','Streaming','Expense',1),
(12,'Yes','SPOTIFY','Subscriptions','Music','Expense',1),
(13,'Yes','APPLE.COM/BILL','Subscriptions','Apple','Expense',1),
(14,'Yes','HULU','Subscriptions','Streaming','Expense',1),
(15,'Yes','PAYROLL','Income','Salary','Income',1),
(16,'Yes','DIRECT DEP','Income','Salary','Income',1),
(17,'Yes','RENT','Housing','Rent / Mortgage','Expense',1),
]

init_db()
with connect() as con:
    con.execute('DELETE FROM category_rules')
    con.executemany('''INSERT INTO category_rules(priority,active,pattern,category,subcategory,transaction_type,recurring) VALUES(?,?,?,?,?,?,?)''', [(a, b=='Yes', c,d,e,f,g) for a,b,c,d,e,f,g in RULES])
print(f'Loaded {len(RULES)} category rules.')
