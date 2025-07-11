import calendar
import os
import pandas as pd
import requests
from flask import Flask, render_template, redirect, url_for
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap5
from datetime import datetime, date

# TODO
# Make the testing loop work for cities name - manage cap

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = 'secret'
month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]
dest_nb = 2
destinations = ['Paris', 'Sydney']

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
Test_city = 'paris'


# ------------------- TESTING LOOP---------------------------
def get_IATA_online():
    global reach_offset_limit, city_found, offset
    while not reach_offset_limit or not city_found:
        IATA_PARAMS = {
            'access_key': IATA_KEY,
            # 'offset': offset, #To remove if search option is available
            'search': Test_city
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


# -------------------------------------------------------------------

def get_IATA(city):
    IATA_MEMORY = pd.read_csv('IATA_memory.csv')
    try:
        IATA_CODE = IATA_MEMORY[IATA_MEMORY['City'] == city.capitalize()]['Code'][0]
    except KeyError:
        print('City not found in CSV.')
        pass  # TODO Call online function
        response = ''
        if response == '200':
            pass
        # if response.status_code == 200:
        #     IATA_CODE = response.json()['data']['iata_code']
        #     IATA_MEMORY.insert(len(IATA_MEMORY['City']), city.capitalize(), IATA_CODE)
        #     IATA_MEMORY.to_csv('IATA_memory.csv')
        else:
            return False
    return IATA_CODE


class DestForm(FlaskForm):
    Destination = StringField('destination', validators=[DataRequired()])
    Add = SubmitField()


@app.route("/", methods=['GET', 'POST'])
def home():
    myForm = DestForm()
    city_error = True  # Put to False
    if myForm.validate_on_submit():
        entry = myForm.Destination.data.capitalize()
        if not get_IATA(entry):
            city_error = True
        else:
            destinations.append(entry)
            print(f'New list of destination {destinations}')
            return redirect(url_for('change_dest', value=True))
    return render_template('index.html', cal=month_names, dest=dest_nb, destinations=destinations, form=myForm,
                           current_year=datetime.now().year, city_error=city_error)


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


@app.route("/remove/<dest>")
def remove_dest(dest):
    global destinations
    destinations.remove(dest)
    print(f'New list of destination {destinations}')
    return redirect(url_for('change_dest', value=False))


@app.route("/search/")
def search_flight():
    IATA_CODE = get_IATA(destinations[0])
    print(IATA_CODE)
    # Get period time
    dates = get_period()

    # KIWI API REQUESTS
    flight_info = {
        'fly_from': IATA_CODE,
        'date_from': dates[0],
        'date_to': dates[1],
    }
    response = requests.get(f'{KIWI_BASE_URL}/search', params=flight_info, headers=KIWI_HEAD)
    print(response.status_code)
    print(response.json())
    return redirect("/")


def get_period():
    current_year = date.today().year
    current_month = date.today().month
    date_from = ''
    date_to = ''
    for x in range(current_month - 1, len(month_names)):  # Starting from the current month
        if date_from == '':
            if month_names[x][1]:
                date_from = f'01/{dformat(x + 1)}/{current_year}'
        else:
            if not month_names[x][1]:
                date_to = f'{calendar.monthrange(current_year, x + 1)[1]}/{dformat(x + 1)}/{current_year}'

    if date_to == '':
        for x in range(current_month - 1):
            if not month_names[x][1]:
                date_to = f'{calendar.monthrange(current_year + 1, x)[1]}/{dformat(x)}/{current_year + 1}'
                break
        if date_to == '':
            date_to = f'{calendar.monthrange(current_year + 1, current_month)[1]}/{dformat(current_month)}/{current_year + 1}'

    print(f'date_from:{date_from}, date_to:{date_to}')
    return date_from, date_to


def dformat(x):
    if x < 10:
        x2 = f'0{x}'
    else:
        x2 = x
    return x2


if __name__ == '__main__':
    app.run()
