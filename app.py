#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import logging
import os
import sys
from logging import FileHandler, Formatter

import babel
import dateutil.parser
from flask import (Flask, Response, flash, redirect, render_template, request,
                   url_for)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form

from forms import *
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

#app = Flask(__name__)
#moment = Moment(app)
#app.config.from_object('config')
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

# TODO: connect to a local postgresql database

#migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#Models in models.py

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  results = Venue.query.distinct(Venue.city, Venue.state).all()
  for result in results:
        city_state_unit = {
            "city": result.city,
            "state": result.state
        }
        venues = Venue.query.filter_by(city=result.city, state=result.state).all()

        # format each venue
        formatted_venues = []
        for venue in venues:
            formatted_venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
            })
        
        city_state_unit["venues"] = formatted_venues
        data.append(city_state_unit)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  response = {}
  venues = list(Venue.query.filter(
      Venue.name.ilike(f"%{search_term}%") |
      Venue.state.ilike(f"%{search_term}%") |
      Venue.city.ilike(f"%{search_term}%") 
  ).all())
  response["count"] = len(venues)
  response["data"] = []

  for venue in venues:
      venue_unit = {
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
      }
      response["data"].append(venue_unit)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  current_time = datetime.now()
  data = {}
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  data["id"] = venue.id
  data["name"] = venue.name
  data["genres"] = venue.genres
  data["address"] = venue.address
  data["city"] = venue.city
  data["state"] = venue.state
  data["phone"] = venue.phone
  data["website"] = venue.website
  data["facebook_link"] = venue.facebook_link
  data["seeking_talent"] = venue.seeking_talent
  data["seeking_description"] = venue.seeking_description
  data["image_link"] = venue.image_link
  data["upcoming_shows"] = []
  data["past_shows"] = []
  
  shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).all()
  for show in shows:
    if show.start_time < current_time: 
      data["past_shows"].append({
        "artist_id": show.artist_id,
        "artist_name": show.artists.name,
        "artist_image_link": show.artists.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    else: 
      data["upcoming_shows"].append({
        "artist_id": show.artist_id,
        "artist_name": show.artists.name,
        "artist_image_link": show.artists.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
      
      
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  form = VenueForm(request.form)

  if form.validate():
      try:
          new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=",".join(form.genres.data), # convert array to string separated by commas
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
            website=form.website_link.data
          )
          db.session.add(new_venue)
          db.session.commit()
          flash('Venue ' + request.form['name'] + ' was successfully listed!')

      except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue' + ' could not be listed.')

      finally:
          db.session.close()
  else:
      print("\n\n", form.errors)
      flash('An error occurred. Venue' + ' could not be listed.')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template(url_for("index"))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash("Venue " + venue.name + " was deleted successfully!")
  except:
      db.session.rollback()
      print(sys.exc_info())
      flash("Venue was not deleted successfully.")
  finally:
      db.session.close()

  return redirect(url_for("index"))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  artists_matching_search_term = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
  current_time = datetime.now()
  response = {
    "count": len(artists_matching_search_term),
    "data": []
  }
  
  for artist in artists_matching_search_term: 
    upcoming_shows = []
    shows = db.session.query(Show).filter(Show.artist_id == artist.id).all()
    
    for show in shows: 
      if show.start_time > current_time: 
        upcoming_shows.append(show)
    
    response["data"].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows)
    })

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  current_time = datetime.now()
  data = {}
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  data["id"] = artist.id
  data["name"] = artist.name
  data["genres"] = artist.genres
  data["city"] = artist.city
  data["state"] = artist.state
  data["phone"] = artist.phone
  data["website"] = artist.website
  data["facebook_link"] = artist.facebook_link
  data["seeking_venue"] = artist.seeking_venue
  data["seeking_description"] = artist.seeking_description
  data["image_link"] = artist.image_link
  data["past_shows"] = []
  data["upcoming_shows"] = []

  shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).all()
  for show in shows: 
    if show.start_time > current_time:
      data["upcoming_shows"].append({
      "venue_id": show.venue_id,
      "venue_name": show.venues.name,
      "venue_image_link": show.venues.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    else: 
      data["past_shows"].append({
      "venue_id": show.venue_id,
      "venue_name": show.venues.name,
      "venue_image_link": show.venues.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  form = ArtistForm(request.form)
  
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  error = False
    
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.image_link = request.form['image_link']
  artist.genres = request.form.getlist('genres')
  artist.facebook_link = request.form['facebook_link']
  artist.website = request.form['website_link']
  artist.seeking_venue = True if 'seeking_venue' in request.form else False
  artist.seeking_description = request.form['seeking_description']
  
  
  try: 
      db.session.commit()
  except: 
      db.session.rollback()
      error = True
      print(sys.exc_info())
  finally: 
      db.session.close()
  if error: 
      flash('Opps! Artist ' + request.form['name'] + ' details not updated successfully.')
  else: 
      flash('Artist ' + request.form['name'] + ' details updated successfully.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  form = VenueForm(request.form)
  
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.image_link = request.form['image_link']
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form['facebook_link']
  venue.website = request.form['website_link']
  venue.seeking_talent = True if 'seeking_talent' in request.form else False
  venue.seeking_description = request.form['seeking_description']
  
  try:
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('Opps! Venue ' + request.form['name'] + ' details not updated successfully.')
  else: 
    flash('Venue ' + request.form['name'] + ' details updated successfully.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  error = False
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']
    
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    
    db.session.add(artist)
    db.session.commit()
  except: 
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else: 
     # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
 
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = db.session.query(Show).all()
  for show in shows: 
    artist = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    venue = db.session.query(Venue).filter(Venue.id == show.venue_id).first()
    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name, # or venue
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error = False
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except: 
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
     # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    flash('An error occurred. Show could not be listed.')
  else: 
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
