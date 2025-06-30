from flask import Flask, render_template
import calendar

app = Flask(__name__)

month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]

@app.route("/")
def home():
    return render_template('index.html', cal=month_names)





if __name__ == '__main__':
    app.run()
