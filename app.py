import datetime as dt
import numpy as np
from numpy.core.arrayprint import DatetimeFormat
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
conn = engine.connect()

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate Analysis API.<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year"""
    session = Session(engine)
    # Calculate the date 1 year ago from last date in database
    last_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    # Query for the date and precipitation for the last year
    results = session.query(measurement.date, measurement.prcp).order_by(measurement.date.desc()).filter(measurement.date >= last_year).all() 
    session.close()
    # Dict with date as the key and prcp as the value
    precipitation_dict = {}
    precipitation = []
    for result in results:
        precipitation_dict = [{result[0]:result[1]}]
        precipitation += precipitation_dict
    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    session = Session(engine)
    results=session.query(station.station).all() 
    session.close()
    # Unravel results into a 1D array and convert to a list
    stations_list = list(np.ravel(results))
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Return the temperature observations (tobs) for previous year."""
    session = Session(engine)
    conn = engine.connect()
    # Calculate the date 1 year ago from last date in database
    last_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    # Query for the date and temperature for the last year
    active_stations_df = pd.read_sql("SELECT station, COUNT(station) FROM measurement GROUP BY station ORDER BY COUNT(station) DESC", conn)
    most_active_station = active_stations_df.loc[0,'station']
    results = session.query(measurement.date, measurement.tobs).order_by(measurement.date.desc()).filter(measurement.date >= last_year).filter(measurement.station==most_active_station)
    session.close()
    # Dict with date as the key and tobs as the value
    temperature_dict = {}
    temperature = []
    for result in results:
        temperature_dict = [{result[0]:result[1]}]
        temperature += temperature_dict
    return jsonify(temperature)

@app.route("/api/v1.0/<start>")
def start(start=None):
    """Return TMIN, TAVG, TMAX."""
    session = Session(engine)
    temps = [measurement.date, 
         func.min(measurement.tobs), 
         func.avg(measurement.tobs), 
         func.max(measurement.tobs)]
    results=session.query(*temps).\
        group_by(measurement.date).order_by(measurement.date).filter(measurement.date >= start).all()
    session.close()
    return jsonify(results)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start=None, end=None):
    session = Session(engine)
    temps = [measurement.date, 
         func.min(measurement.tobs), 
         func.avg(measurement.tobs), 
         func.max(measurement.tobs)]
    results=session.query(*temps).\
        group_by(measurement.date).order_by(measurement.date).filter(measurement.date >= start).filter(measurement.date <= end).all()
    session.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)