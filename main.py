import calendar
import os
import requests

from flask import Flask, render_template, redirect

app = Flask(__name__)

month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]
destination = 1

Key = os.environ.get('API_KEY')
URL = 'https://api.tequila.kiwi.com/v2'

headers = {
    'apikey': Key,
}


# TODO Create for for destination
# Implement the form in HTML
# Get the data in change destination and store it :
dest = []
# Retrieve dests and date for API request


@app.route("/")
def home():
    return render_template('index.html', cal=month_names, dest=destination)

@app.route("/update_period/<month_id>")
def update_period(month_id):
    # Recreate the list via list-comprehension
    global month_names
    month_names = [(m, not v) if m == month_id else (m, v)
                   for m, v in month_names]
    return redirect("/")

@app.route("/change_dest/<value>")
def change_dest(value):
    global destination
    if value == 'True':
        destination += 1
    elif destination > 0:
        destination -= 1
    print(f'Based on :{value} - Nb dest changed:{destination}')
    return redirect("/")

@app.route("/search/<dests>")
def search_flight(dests):
    print(dests)
    flight_info = {
        'fly_from': 'LON',
        'date_from': '01/09/2025',
        'date_to': '01/10/2025',
    }

    #response = requests.get(f'{URL}/search', params=flight_info, headers=headers)
    #print(response.status_code)
    #print(response.json())
    return redirect("/")

if __name__ == '__main__':
    app.run()
