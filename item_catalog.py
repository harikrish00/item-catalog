from flask import Flask, url_for, render_template, request, flash, redirect, jsonify
from flask import session as login_session, g
from flask_script import Manager
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker
from forms import CatalogForm, ItemForm, SignupForm, LoginForm
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_bootstrap import Bootstrap
from setup_database import Base, Item, Catalog, User
from flask.ext.script import Shell
import random,string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from login_helper import login_required

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Application initialization
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super secret'
manager = Manager(app)
bootstrap = Bootstrap(app)

# Connect to database and create a session
# engine = create_engine("sqlite:///itemcatalog.db")
engine = create_engine("postgresql://catalogex:Welcome@localhost:5432/itemcatalog")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

def make_shell_context():
    return dict(app=app, engine=engine, session=session, User=User,
                Catalog=Catalog, Item=Item)
manager.add_command("shell", Shell(make_context=make_shell_context))

@app.before_request
def load_user():
    if 'user_id' in login_session:
        user = session.query(User).filter_by(id=login_session["user_id"]).first()
    else:
        user = None  # Make it better, use an anonymous User instead
    g.user = user

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        user = session.query(User).filter_by(username=username).one()
        if user is not None and user.verify_password(form.password.data):
            login_session['user_id'] = user.id
            login_session['username'] = user.username
            login_session['email'] = user.email
            login_session['name'] = user.name
            flash('You are successfully signed in','success')
            return redirect(url_for('index'))
        else:
            flash('Your username or password is incorrect!')
            return redirect(url_for('login'))
    state = ''.join(random.choice(string.ascii_uppercase +
      string.digits)for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, form=form)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['name'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'], "success")
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=['POST'])
def fbconnect():

    # Before processing request verify the state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s" % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['name'] = data['name']
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    # Compose response output html for welcome message
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; \
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'], "success")
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/logout')
def logout():
    if 'user_id' in login_session:
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        if 'provider' in login_session:
            if login_session['provider'] == 'google':
                gdisconnect()
                del login_session['gplus_id']
                del login_session['access_token']
            if login_session['provider'] == 'facebook':
                fbdisconnect()
                del login_session['facebook_id']
        # common session info for both the providers
            # del login_session['name']
            del login_session['picture']
            del login_session['provider']
        flash("You have successfully been logged out.","success")
        return redirect(url_for('index'))
    else:
        flash("You were not logged in")
        return redirect(url_for('ndex'))

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
    return jsonify(catalogs=[c.serialize for c in catalogs])

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
    items = get_recent_items()
    return render_template("index.html",catalogs=catalogs, items=items)

# Create new catalog
@app.route('/catalogs/new', methods = ['GET','POST'])
@login_required
def new_catalog():
    form = CatalogForm()
    if request.method == 'POST':
        name = request.form['name']
        # Prevent duplicate catalogs being created
        if session.query(exists().where(Catalog.name==name)).scalar():
            flash("Catalog already exists","danger")
            return render_template('new_catalog.html', form=form)
        user_id = login_session['user_id']
        catalog = Catalog(name=name, user_id=user_id)
        session.add(catalog)
        session.commit()
        flash('New catalog has been added !','success')
        return redirect(url_for('index'))
    else:
        return render_template('new_catalog.html', form=form)

@app.route('/catalogs/<catalog_name>/edit', methods = ['GET','POST'])
@login_required
def edit_catalog(catalog_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    message = is_catalog_author(catalog)
    if message:
        return message
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
@login_required
def delete_catalog(catalog_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    message = is_catalog_author(catalog)
    if message:
        return message
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
@login_required
def new_catalog_item(catalog_name):
    form = ItemForm()
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    message = is_catalog_author(catalog)
    if message:
        return message
    if form.validate_on_submit():
        name = request.form['name']
        if session.query(Item).filter(Item.name==name,Item.catalog_id==catalog.id).count():
            flash("Item already exists!","danger")
            return render_template('new_item.html',form=form, catalog=catalog)
        description = request.form['description']
        price = request.form['price']
        item = Item(name=name, description=description,
                    price=price, catalog_id=catalog.id)
        session.add(item)
        session.commit()
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('new_item.html',form=form, catalog=catalog)

@app.route('/catalogs/<catalog_name>/items/<item_name>/edit',
            methods = ['GET','POST'])
@login_required
def edit_catalog_item(catalog_name, item_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    message = is_catalog_author(catalog)
    if message:
        return message
    item = session.query(Item).filter_by(catalog_id=catalog.id,
                                            name=item_name).one()
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        item.name = request.form['name']
        item.description = request.form['description']
        item.price = request.form['price']
        session.add(item)
        session.commit()
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('new_item.html',form=form, catalog=catalog, item=item)

@app.route('/catalogs/<catalog_name>/items/<item_name>/delete',
            methods = ['GET','POST'])
@login_required
def delete_catalog_item(catalog_name, item_name):
    catalog = session.query(Catalog).filter_by(name=catalog_name).one()
    message = is_catalog_author(catalog)
    if message:
        return message
    item = session.query(Item).filter_by(catalog_id=catalog.id, name=item_name).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item has been successfully deleted !','success')
        return redirect(url_for('catalog_items',catalog_name=catalog_name))
    return render_template('delete_item.html',catalog=catalog, item=item)

def is_catalog_author(catalog):
    print catalog.user_id,">>",login_session['user_id']
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to \
        edit this catalog. Please create your own restaurant in order to edit.');\
         window.location.href = '/' }</script><body onload='myFunction()''>"

def create_user(login_session):
    # Create user in the database when they login
    newUser = User(name=login_session['username'],
                username=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def get_recent_items():
    return [ item for item in session.query(Item).order_by('timestamp desc').all()]

if __name__ == '__main__':
    manager.run()
