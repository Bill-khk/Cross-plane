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
destinations = []

# KIWI API
KIWI_KEY = os.environ.get('API_KEY')
KIWI_BASE_URL = 'https://api.tequila.kiwi.com/v2'
KIWI_HEAD = {
    'apikey': KIWI_KEY,
}

# AVIATION STACK API
IATA_KEY = os.environ.get('IATA_KEY')
IATA_BASE_URL = 'https://api.aviationstack.com/v1/'
offset = 0
city_found = False
reach_offset_limit = False
Test_city = 'Paris'

# TODO Fix that

while not reach_offset_limit or not city_found:
    IATA_PARAMS = {
        'access_key': IATA_KEY,
        'offset': offset
    }
    IATA_RESPONSE = requests.get(f'{IATA_BASE_URL}cities', params=IATA_PARAMS)
    print(f'for offset:{offset} - Code:{IATA_RESPONSE.status_code}')
    IATA_CITIES = IATA_RESPONSE.json()['data']
    offset_limit = int(IATA_RESPONSE.json()['pagination']['total'] / 100)  # Used to know the max nb of loop request

    for entry in IATA_CITIES:
        if entry['city_name'] == Test_city:  # City found
            print(entry['iata_code'])
            city_found = True
            # TODO Put in a CSV file to save the previous research

    if not city_found:
        # Try for the next 100 cities
        offset += 100
        if offset > offset_limit:
            reach_offset_limit = True


class DestForm(FlaskForm):
    Destination = StringField('destination', validators=[DataRequired()])
    Add = SubmitField()


# TODO Create for for destination
# Implement the form in HTML
# Get the data in change destination and store it :
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

    # response = requests.get(f'{KIWI_BASE_URL}/search', params=flight_info, headers=KIWI_HEAD)
    # print(response.status_code)
    # print(response.json())
    # return redirect("/")


@app.route("/IATA/<dests>")
def IATA_conversion(dests):
    IATA_KEY = os.environ.get('IATA_KEY')
    IATA_BASE_URL = 'https://api.aviationstack.com/v1/'
    IATA_HEAD = {
        'access_key': IATA_KEY,
    }
    # Using https://aviationstack.com/


if __name__ == '__main__':
    app.run()
