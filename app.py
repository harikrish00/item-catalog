from flask import Flask

# Application initialization
app = Flask(__name__)

@app.route('/')
def index():
    return "<h1> Hello World !</h1>"

if __name__ == '__main__':
    app.secret_key = "Super secret"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
