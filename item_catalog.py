from flask import Flask, url_for, render_template, request, flash, redirect
from flask_script import Manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from forms import CatalogForm, ItemForm
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_bootstrap import Bootstrap
from setup_database import Base, Item, Catalog, User
from flask.ext.script import Shell


# Application initialization
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'
manager = Manager(app)
bootstrap = Bootstrap(app)


# Connect to database and create a session
engine = create_engine("sqlite:///itemcatalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

def make_shell_context():
    return dict(app=app, engine=engine, session=session, User=User, Catalog=Catalog, Item=Item)
manager.add_command("shell", Shell(make_context=make_shell_context))

# Home page or Catalog Index Page
@app.route('/')
@app.route('/catalogs')
def index():
    catalogs = session.query(Catalog).all()
    return render_template("index.html",catalogs=catalogs)

@app.route('/login')
def login():
    return "<h1>login or register</h1>"

@app.route('/logout')
def logout():
    return "<h1>Logged out ...</h1>"

# Create new catalog
@app.route('/catalogs/new', methods = ['GET','POST'])
def new_catalog():
    form = CatalogForm()
    if request.method == 'POST':
        name = request.form['name']
        catalog = Catalog(name=name)
        session.add(catalog)
        session.commit()
        flash('New catalog has been added')
        return redirect(url_for('index'))
    else:
        return render_template('new_catalog.html', form=form)

@app.route('/catalogs/<catalog_name>/edit', methods = ['GET','POST'])
def edit_catalog(catalog_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    form = CatalogForm()
    form.name.data = catalog.name
    if request.method == 'POST':
        name = request.form['name']
        catalog.name = name
        session.add(catalog)
        session.commit()
        flash('Catalog name has been updated !','success')
        return redirect(url_for('index'))
    else:
        return render_template('edit_catalog.html',form=form, catalog=catalog)


@app.route('/catalogs/<catalog_name>/delete', methods = ['GET','POST'])
def delete_catalog(catalog_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    if request.method == 'POST':
        session.delete(catalog)
        session.commit()
        flash('Item has been successfully deleted !','success')
        return redirect(url_for('index'))
    return render_template('delete_catalog.html',catalog=catalog)

@app.route('/catalogs/<catalog_name>/items')
def catalog_items(catalog_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    items = session.query(Item).filter_by(catalog_id=catalog.id).all()
    return render_template('catalog_items.html',catalog=catalog,items=items)

@app.route('/catalogs/<catalog_name>/items/<item_name>')
def catalog_item(catalog_name, item_name):
    return "<h1> Description: %s contains item %s </h1>" % (catalog_name, item_name)

@app.route('/catalogs/<catalog_name>/items/new', methods = ['GET','POST'])
def new_catalog_item(catalog_name):
    form = ItemForm()
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    if form.validate_on_submit():
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        item = Item(name=name, description=description, price=price, catalog_id=catalog.id)
        session.add(item)
        session.commit()
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('new_item.html',form=form)


@app.route('/catalogs/<catalog_name>/items/<item_name>/edit', methods = ['GET','POST'])
def edit_catalog_item(catalog_name, item_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    item = session.query(Item).filter_by(catalog_id=catalog.id, name=item_name).one()
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        item.name = request.form['name']
        item.description = request.form['description']
        item.price = request.form['price']
        session.add(item)
        session.commit()
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('new_item.html',form=form, catalog=catalog, item=item)


@app.route('/catalogs/<catalog_name>/items/<item_name>/delete', methods = ['GET','POST'])
def delete_catalog_item(catalog_name, item_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    item = session.query(Item).filter_by(catalog_id=catalog.id, name=item_name).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item has been successfully deleted !','success')
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('delete_item.html',catalog=catalog, item=item)


if __name__ == '__main__':
    manager.run()
