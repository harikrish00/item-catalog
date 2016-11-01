from flask import Flask, url_for, render_template, request, flash, redirect, jsonify
from flask_script import Manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from forms import CatalogForm, ItemForm, SignupForm, LoginForm
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_bootstrap import Bootstrap
from setup_database import Base, Item, Catalog, User
from flask.ext.script import Shell
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required

# Application initialization
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'
manager = Manager(app)
bootstrap = Bootstrap(app)

# login manager and sessions
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).filter_by(id=user_id).one()

# Connect to database and create a session
engine = create_engine("sqlite:///itemcatalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

def make_shell_context():
    return dict(app=app, engine=engine, session=session, User=User, Catalog=Catalog, Item=Item)
manager.add_command("shell", Shell(make_context=make_shell_context))

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        user = session.query(User).filter_by(username=username).one()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            flash('You are successfully signed in','success')
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(name=form.name.data, username=form.username.data,
                    password=form.password.data,email=form.email.data)
        session.add(user)
        session.commit()
        flash('Thanks for registering')
        return redirect(url_for('index'))
    return render_template('signup.html', form=form)

@app.route('/catalogs/JSON')
def catalogs_json():
    catalogs = session.query(Catalog).all()
    return jsonify(catalogs=[c.serialize for c in catalog])

@app.route('/catalogs/<catalog_name>/JSON')
def catalog_json(catalog_name):
    try:
        catalog = session.query(Catalog).filter_by(name=catalog_name).one()
        return jsonify(catalog=catalog.serialize)
    except:
        return "Sorry no data found"

@app.route('/catalogs/<catalog_name>/items/JSON')
def catalog_items_json(catalog_name):
    try:
        catalog = session.query(Catalog).filter_by(name=catalog_name).one()
        items = session.query(Item).filter_by(catalog_id=catalog.id).all()
        return jsonify(catalog=[i.serialize for i in items])
    except:
        return "Sorry no data found"

@app.route('/catalogs/<catalog_name>/items/<item_name>/JSON')
def catalog_item_json(catalog_name, item_name):
    try:
        catalog = session.query(Catalog).filter_by(name=catalog_name).one()
        item = session.query(Item).filter_by(catalog_id=catalog.id, name=item_name).one()
        return jsonify(catalog=item.serialize)
    except:
        return "Sorry no data found"

# Home page or Catalog Index Page
@app.route('/')
@app.route('/catalogs')
def index():
    catalogs = session.query(Catalog).all()
    return render_template("index.html",catalogs=catalogs)

# Create new catalog
@app.route('/catalogs/new', methods = ['GET','POST'])
@login_required
def new_catalog():
    form = CatalogForm()
    if request.method == 'POST':
        name = request.form['name']
        user_id = current_user.id
        print "--->",user_id
        catalog = Catalog(name=name, user_id=user_id)
        session.add(catalog)
        session.commit()
        flash('New catalog has been added !','success')
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
