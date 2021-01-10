from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired
import requests
import simplejson as json
import datetime
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap(app)

def make_graph(ticker, month, year):
    url = ("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
    + "&symbol="
    + ticker
    + "&outputsize=full&apikey="
    + os.getenv('API_KEY'))
    full_data = json.loads(requests.get(url).text)
    if "Error Message" in full_data:
        return 1

    all_dates = map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'),
                    full_data['Time Series (Daily)'].keys())
    month_year = datetime.datetime.strptime(month + ' ' + year, '%B %Y')

    dates = []
    for date in all_dates:
        if date.month == month_year.month and date.year == month_year.year:
            dates.append(date)
    dates = sorted(dates)

    prices = []
    for date in dates:
        date_string = date.strftime('%Y-%m-%d')
        price = full_data['Time Series (Daily)'][date_string]['4. close']
        price = float(price)
        prices.append(price)

    t = ("Closing Prices of " + ticker + " for the month of " + month + " "
         + year)
    p = figure(x_axis_type="datetime", title=t)
    p.grid.grid_line_alpha=0.3
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Price'

    p.line(dates, prices, legend_label=ticker, color="black")
    p.legend.location = "top_right"

    return(p)

class StockForm(FlaskForm):
    ticker = StringField('Enter stock ticker code (e.g., AAPL):', validators=[DataRequired()])
    month = DateField('Enter month (MM/YYYY):', format='%m/%Y', validators=[DataRequired()])
    submit = SubmitField('Display Closing Price')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = StockForm()
    output = ""
    if form.validate_on_submit():
        ticker = form.ticker.data
        date = form.month.data
        month = date.strftime('%B')
        year = date.strftime('%Y')
        p = make_graph(ticker, month, year)
        if p == 1:
            output = "Unable to obtain data. Invalid stock ticker?"
        else:
            script, div = components(p)
            output = script + div

    return render_template('index.html', form=form, output=output)

if __name__ == '__main__':
  app.run(port=33507)
