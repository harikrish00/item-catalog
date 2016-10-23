from flask import Flask, url_for
from flask_script import Manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Application initialization
app = Flask(__name__)
manager = Manager(app)

# Connect to database and create a session
engine = create_engine("sqlite:///itemcatalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/catalogs')
def index():
    return "<h1> Catalog List </h1>"

@app.route('/login')
def login():
    return "<h1>login or register</h1>"

@app.route('/logout')
def logout():
    return "<h1>Logged out ...</h1>"

@app.route('/catalogs/new')
def new_catalog():
    return "<h1> New catalog </h1>"

@app.route('/catalogs/<catalog_name>/edit', methods = ['GET','POST'])
def edit_catalog(catalog_name):
    return "<h1> Edit a catalog</h1>"

@app.route('/catalogs/<catalog_name>/delete', methods = ['GET','POST'])
def delete_catalog(catalog_name):
    return "<h1> Delete a catalog </h1>"

@app.route('/catalogs/<catalog_name>/items')
def catalog_items(catalog_name):
    return "<h1> %s items </h1>" % catalog_name

@app.route('/catalogs/<catalog_name>/items/<item_name>')
def catalog_item(catalog_name, item_name):
    return "<h1> Description: %s contains item %s </h1>" % (catalog_name, item_name)

@app.route('/catalogs/<catalog_name>/items/new', methods = ['GET','POST'])
def new_catalog_item(catalog_name):
    return "<h1> New: %s contains item </h1>" % (catalog_name)

@app.route('/catalogs/<catalog_name>/items/<item_name>/edit', methods = ['GET','POST'])
def edit_catalog_item(catalog_name, item_name):
    return "<h1> Edit: %s contains item %s </h1>" % (catalog_name, item_name)

@app.route('/catalogs/<catalog_name>/items/<item_name>/delete', methods = ['GET','POST'])
def delete_catalog_item(catalog_name, item_name):
    return "<h1> Delete: %s contains item %s </h1>" % (catalog_name, item_name)


if __name__ == '__main__':
    manager.run()
