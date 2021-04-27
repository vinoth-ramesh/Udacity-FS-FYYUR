#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import os
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

from flask_migrate import Migrate
from dotenv import load_dotenv
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

load_dotenv()

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app,db)

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
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  adata = []

  for area in areas:
    venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    vdata = []
    for venue in venues:
      vdata.append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==venue.id).filter(Show.show_time>=datetime.now()).all())
      })
    adata.append({
      "city": area.city,
      "state": area.state, 
      "venues": vdata
    })
  return render_template('pages/venues.html', areas=adata);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_text = request.form.get('search_term', '')
  results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_text}%')).all()
  data = []

  for result in results:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.show_time >= datetime.now()).all()),
    })
  
  output={
    "count": len(results),
    "data": data
  }
  return render_template('pages/search_venues.html', results=output, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
# def show_venue(venue_id):
#   # shows the venue page with the given venue_id
#   # TODO: replace with real venue data from the venues table, using venue_id

def show_venue(venue_id):
  
  venue = Venue.query.get(venue_id)

  if not venue: 
    return render_template('errors/404.html')

  upcoming_shows_data = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.show_time>=datetime.now()).all()
  upcoming_shows = []

  past_shows_data = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.show_time<datetime.now()).all()
  past_shows = []

  for show in past_shows_data:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in upcoming_shows_data:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.show_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

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
  err_flg = False
  
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_talent = True if 'seeking_talent' in request.form else False 
    seeking_description = request.form['seeking_description']

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()

  except: 
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()

  if err_flg: 
    flash('An error happened. Venue ' + request.form['name']+ ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  err_flg = False

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()

  except:
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if err_flg: 
    flash(f'An error happened. Venue {venue_id} could not be deleted.')
  else: 
    flash(f'Venue {venue_id} was successfully deleted.')

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  data = db.session.query(Artist).all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_text = request.form.get('search_term', '')
  results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_text}%')).all()
  data = []

  for result in results:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.show_time >= datetime.now()).all()),
    })
  
  output={
    "count": len(results),
    "data": data
  }
  return render_template('pages/search_artists.html', results=output, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist_data = db.session.query(Artist).get(artist_id)

  if not artist_data: 
    return render_template('errors/404.html')

  past_shows_data = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.show_time<datetime.now()).all()
  past_shows = []

  for show in past_shows_data:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_shows_data = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.show_time>=datetime.now()).all()
  upcoming_shows = []

  for show in upcoming_shows_data:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })


  data = {
    "id": artist_data.id,
    "name": artist_data.name,
    "genres": artist_data.genres,
    "city": artist_data.city,
    "state": artist_data.state,
    "phone": artist_data.phone,
    "website_link": artist_data.website_link,
    "facebook_link": artist_data.facebook_link,
    "seeking_venue": artist_data.seeking_venue,
    "seeking_description": artist_data.seeking_description,
    "image_link": artist_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
 
  # TODO: populate form with fields from artist with ID <artist_id>

  artist = Artist.query.get(artist_id)

  if artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  err_flg = False  
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()

  except: 
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()

  if err_flg: 
    flash('An error happened. Artist could not be updated.')
  else: 
    flash('Artist was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  err_flg = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()

  except: 
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()

  if err_flg: 
    flash(f'An error happened. Venue could not be updated.')
  else:
    flash(f'Venue was updated successfully!')

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
  err_flg = False

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

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()

  except: 
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()
  
  if err_flg: 
    flash('An error happened. Artist ' + request.form['name']+ ' could not be created.')
  else: 
  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
 
  shows_data = db.session.query(Show).join(Artist).join(Venue).all()

  data = []
  for show in shows_data: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.show_time.strftime('%Y-%m-%d %H:%M:%S')
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
  err_flg = False
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    show_time = request.form['start_time']

    print(request.form)

    show = Show(artist_id=artist_id, venue_id=venue_id, show_time=show_time)
    db.session.add(show)
    db.session.commit()

  except: 
    err_flg = True
    db.session.rollback()
    print(sys.exc_info())

  finally: 
    db.session.close()

  if err_flg: 
    flash('An error happened. Show could not be created.')
  else: 
  # on successful db insert, flash 
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
