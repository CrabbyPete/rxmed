from flask import Flask, render_template

application = Flask(__name__,static_url_path='/static')

@application.route('/')
def home():
    return render_template( 'home.html')


if __name__ == "__main__":
    application.run(host='localhost', port=5000, debug=True)