import calendar
import os
import requests
from flask import Flask, render_template, redirect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap5
from datetime import datetime


app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = 'secret'
month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]
dest_nb = 1
destination = []

# API
Key = os.environ.get('API_KEY')
URL = 'https://api.tequila.kiwi.com/v2'
headers = {
    'apikey': Key,
}


class DestForm(FlaskForm):
    Destination = StringField('destination', validators=[DataRequired()])
    Add = SubmitField()


# TODO Create for for destination
# Implement the form in HTML
# Get the data in change destination and store it :
dest = []


# Retrieve dests and date for API request


@app.route("/", methods=['GET', 'POST'])
def home():
    myForm = DestForm()
    if myForm.validate_on_submit():
        print(myForm.Destination.data)
        redirect("/")
    return render_template('index.html', cal=month_names, dest=dest_nb, form=myForm, current_year=datetime.now().year)


@app.route("/update_period/<month_id>")
def update_period(month_id):
    # Recreate the list via list-comprehension
    global month_names
    month_names = [(m, not v) if m == month_id else (m, v)
                   for m, v in month_names]
    return redirect("/")


@app.route("/change_dest/<value>")
def change_dest(value):
    global dest_nb
    if value == 'True':
        dest_nb += 1
    elif dest_nb > 0:
        dest_nb -= 1
    print(f'Based on :{value} - Nb dest changed:{dest_nb}')
    return redirect("/")


@app.route("/search/<dests>")
def search_flight(dests):
    print(dests)

    flight_info = {
        'fly_from': 'LON',
        'date_from': '01/09/2025',
        'date_to': '01/10/2025',
    }

    response = requests.get(f'{URL}/search', params=flight_info, headers=headers)
    print(response.status_code)
    print(response.json())
    return redirect("/")


if __name__ == '__main__':
    app.run()
