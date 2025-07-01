from flask import Flask, render_template, redirect
import calendar

app = Flask(__name__)

month_names = [(month, True) for month in list(calendar.month_abbr)[1:]]
print(month_names)

# TODO :
# 1 - HTML - Add destination button
# 2 - Managing Airport list names and suggestion
# 3 - Connecting to the API
# 4 - Look for Plane for this destination
# 5 - Display best options
# 6 - Add another destination
# 7 - Display best options based on both destination

@app.route("/")
def home():
    return render_template('index.html', cal=month_names)

@app.route("/update_period/<month_id>")
def update_period(month_id):
    # Recreate the list via list-comprehension
    global month_names
    month_names = [(m, not v) if m == month_id else (m, v)
                   for m, v in month_names]
    return redirect("/")


if __name__ == '__main__':
    app.run()
