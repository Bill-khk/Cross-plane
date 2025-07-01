from flask import Flask, render_template, redirect
import calendar

app = Flask(__name__)

month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]
print(month_names)

@app.route("/")
def home():
    return render_template('index.html', cal=month_names)

@app.route("/update_period/<month_id>")
def update_period(month_id):
    # TODO Update the BOL value on the returned month
    return redirect("/")


if __name__ == '__main__':
    app.run()
