import os
from flask import Flask, render_template

cwd = os.getcwd()
print(cwd)
app = Flask(__name__)

@app.route('/')
def index():
    logo_image = os.path.join("static", "logo.jpg")
    return render_template("index.html", logo_image=logo_image)

if __name__ == '__main__':
	app.run()

