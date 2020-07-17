#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime
import itertools
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

VenueGenres = db.Table('venue_genres',
                       db.Column('venue_id', db.Integer,
                                 db.ForeignKey('venues.id')),
                       db.Column('genre_id', db.Integer,
                                 db.ForeignKey('genres.id'))
                       )

ArtistGenres = db.Table('artist_genres',
                        db.Column('artist_id', db.Integer,
                                  db.ForeignKey('artists.id')),
                        db.Column('genre_id', db.Integer,
                                  db.ForeignKey('genres.id'))
                        )


class Genres(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

    def __repr__(self):
        return self.name


class City(db.Model):
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'))
    venues = db.relationship("Venue", backref='city', lazy=True)
    artists = db.relationship("Artist", backref='city', lazy=True)

    def __repr__(self):
        return "%s" % self.name


class State(db.Model):
    __tablename__ = 'states'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cities = db.relationship("City", backref='state', lazy=True)

    def __repr__(self):
        return "%s" % self.name


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship("Show", backref='venue', lazy=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    genres = db.relationship(
        'Genres', secondary=VenueGenres, backref='venues', lazy=True)

    def __repr__(self):
        return "<Venue (name='%s')>" % (self.name)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    website = db.Column(db.String(120))
    shows = db.relationship("Show", backref='artist', lazy=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    genres = db.relationship(
        'Genres', secondary=ArtistGenres, backref='artists', lazy=True)

    def __repr__(self):
        return "<Artist(name='%s')>" % self.name


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)

    def __repr__(self):
        return "<Show (start_time='%s')>" % format_datetime(self.start_time)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

def getVenueUpcomingShows(venue):
    upcoming_shows = []
    shows = Show.query.filter(Show.venue_id == venue.id).all()
    now = datetime.datetime.now().replace(microsecond=0)

    for show in shows:
        if show.start_time >= now:
            upcoming_shows.append(
                {
                    'artist_id': show.artist.id,
                    'artist_name': show.artist.name,
                    'artist_image_link': show.artist.image_link,
                    'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
    return upcoming_shows


def getVenuePastShows(venue):
    past_shows = []
    shows = Show.query.filter(Show.venue_id == venue.id).all()
    now = datetime.datetime.now().replace(microsecond=0)

    for show in shows:
        if show.start_time < now:
            past_shows.append(
                {
                    'artist_id': show.artist.id,
                    'artist_name': show.artist.name,
                    'artist_image_link': show.artist.image_link,
                    'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
    return past_shows


def getArtistUpcomingShows(artist):
    upcoming_shows = []
    shows = Show.query.filter(Show.artist_id == artist.id).all()
    now = datetime.datetime.now().replace(microsecond=0)

    for show in shows:
        if show.start_time >= now:
            upcoming_shows.append(
                {
                    'venue_id': show.venue.id,
                    'venue_name': show.venue.name,
                    'venue_image_link': show.venue.image_link,
                    'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
    return upcoming_shows


def getArtistPastShows(artist):
    past_shows = []
    shows = Show.query.filter(Show.artist_id == artist.id).all()
    now = datetime.datetime.now().replace(microsecond=0)

    for show in shows:
        if show.start_time < now:
            past_shows.append(
                {
                    'venue_id': show.venue.id,
                    'venue_name': show.venue.name,
                    'venue_image_link': show.venue.image_link,
                    'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
    return past_shows


def getOrInsertState(value):
    state_exist = State.query.filter(
        State.name == value).first()
    state = state_exist if state_exist is not None else State(
        name=value)
    return state


def getOrInsertCity(value, state):
    city_exist = City.query.filter(
        City.name == value, City.state_id == state.id).first()
    city = city_exist if city_exist is not None else City(
        name=value, state=state)
    return city


def getOrInsertGenres(values):
    genres = []
    for item in values:
        genres_exist = Genres.query.filter(Genres.name == item).first()
        genres.append(
            genres_exist if genres_exist is not None else Genres(name=item))
    return genres


@app.route('/venues')
def venues():
    data = []
    for item in City.query.all():
        venues = item.venues
        for venue in venues:
            venue.upcoming_shows_count = len(getVenueUpcomingShows(venue))

        data.append({
            'city': item.name,
            'state': item.state,
            'venues': venues
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    query = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
    response = {
        "count": query.count(),
        "data": query.all()
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    upcomingShows = getVenueUpcomingShows(venue)
    pastShows = getVenuePastShows(venue)
    genres = []
    for g in venue.genres:
        genres.append(g.name)
    data = {
        'id': venue.id,
        'name': venue.name,
        'city': venue.city,
        'state': venue.city.state,
        'upcoming_shows_count': len(upcomingShows),
        'upcoming_shows': upcomingShows,
        'past_shows': pastShows,
        'past_shows_count': len(pastShows),
        'genres': genres,
        'facebook_link': venue.facebook_link,
        'website': venue.website,
        'image_link': venue.image_link,
        'address': venue.address,
        'phone': venue.phone,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description
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
    try:
        form = request.form
        state = getOrInsertState(form.get('state'))
        city = getOrInsertCity(form.get('city'), state)
        city.state = state
        genres = getOrInsertGenres(form.getlist('genres'))

        venue = Venue(name=form.get('name'), city=city, address=form.get(
            'address'), phone=form.get('phone'), facebook_link=form.get('facebook_link'), genres=genres)

        db.session.commit()
    except:
        flash('An error occurred. Venue ' +
              form.get('name') + ' could not be listed.')
        db.session.rollback()
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        for show in venue.shows:
            db.session.delete(show)

        db.session.delete(venue)
        db.session.commit()
    except():
        flash('An error occurred. Venue ' +
              venue_id + ' could not be listed.')
        db.session.rollback()
        error = True
    else:
        flash('Venue was successfully deleted!')
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
    response = {
        "count": query.count(),
        "data": query.all()
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    upcomingShows = getArtistUpcomingShows(artist)
    pastShows = getArtistPastShows(artist)
    genres = []
    for g in artist.genres:
        genres.append(g.name)

    data = {
        'id': artist.id,
        'name': artist.name,
        'city': artist.city,
        'state': artist.city.state,
        'upcoming_shows_count': len(upcomingShows),
        'upcoming_shows': upcomingShows,
        'past_shows': pastShows,
        'past_shows_count': len(pastShows),
        'genres': genres,
        'facebook_link': artist.facebook_link,
        'website': artist.website,
        'image_link': artist.image_link,
        'phone': artist.phone,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = Artist.query.get(artist_id)
    artist.state = artist.city.state

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    form = request.form
    try:
        artist = Artist.query.get(artist_id)
        artist.name = form.get('name')
        state = getOrInsertState(form.get('state'))
        artist.city = getOrInsertCity(form.get('city'), state)
        artist.city.state = state
        artist.genres = getOrInsertGenres(form.getlist('genres'))
        artist.phone = form.get('phone')
        artist.facebook_link = form.get('facebook_link')

        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.get(venue_id)
    venue.state = venue.city.state

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    form = request.form
    try:
        venue = Venue.query.get(venue_id)
        venue.name = form.get('name')
        state = getOrInsertState(form.get('state'))
        venue.city = getOrInsertCity(form.get('city'), state)
        venue.city.state = state
        venue.genres = getOrInsertGenres(form.getlist('genres'))
        venue.phone = form.get('phone')
        venue.address = form.get('address')
        venue.facebook_link = form.get('facebook_link')

        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        form = request.form
        artist = Artist(
            name=form.get('name'),
            facebook_link=form.get('facebook_link'),
            phone=form.get('phone'),
        )
        artist.genres = getOrInsertGenres(form.getlist('genres'))
        state = getOrInsertState(form.get('state'))
        artist.city = getOrInsertCity(form.get('city'), state)

        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              form.get('name') + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    for item in shows:
        data.append({
            'venue_id': item.venue.id,
            'venue_name': item.venue.name,
            'artist_id': item.artist.id,
            'artist_name': item.artist.name,
            'artist_image_link': item.artist.image_link,
            'start_time': item.start_time.isoformat()
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
    try:
        form = request.form
        venue = Venue.query.get(form.get('venue_id'))
        artist = Artist.query.get(form.get('artist_id'))
        if venue is None:
            raise ValueError('Venue id is not listed.')
        elif artist is None:
            raise ValueError('Artist id is not listed.')

        newShow = Show(start_time=form.get('start_time'))
        newShow.artist = artist
        newShow.venue = venue

        db.session.add(newShow)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        flash(err.args if err.args else 'An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


@app.cli.command("initdb")
def reset_db():
    """"Drops and Creates fresh database"""

    db.drop_all()
    db.create_all()

    print("Initialized default DB")


@app.cli.command('bootstrap')
def bootstrap_data():
    """Populates database with data"""

    db.drop_all()
    db.create_all()

    st1 = State(name="CA")
    st2 = State(name="NY")

    c1 = City(name="San Francisco", state=st1)
    c2 = City(name="New York", state=st2)

    g1 = Genres(name="jazz")
    g2 = Genres(name="pop")
    g3 = Genres(name="country")
    g4 = Genres(name="R&B")

    v1 = Venue(name="The Musical Hop",
               address="1015 Folsom Street", phone="123-123-1234",
               website="https://www.themusicalhop.com",
               facebook_link="https://www.facebook.com/TheMusicalHop",
               image_link="https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
               seeking_talent=True,
               seeking_description="We are on the lookout for a local artist to play every two weeks. Please call us.",
               )

    v2 = Venue(name="The Dueling Pianos Bar",
               address="1015 Folsom Street", phone="123-123-1234",
               website="https://www.themusicalhop.com",
               facebook_link="https://www.facebook.com/TheMusicalHop",
               image_link="https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
               seeking_talent=True,
               seeking_description="We are on the lookout for a local artist to play every two weeks. Please call us.",
               )

    v3 = Venue(name="The Dueling",
               address="1015 Folsom Street", phone="123-123-1234",
               website="https://www.themusicalhop.com",
               facebook_link="https://www.facebook.com/TheMusicalHop",
               image_link="https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
               seeking_talent=True,
               seeking_description="We are on the lookout for a local artist to play every two weeks. Please call us.",
               )

    v4 = Venue(name="Park Square Live Music & Coffee",
               address="1015 Folsom Street", phone="123-123-1234",
               website="https://www.themusicalhop.com",
               facebook_link="https://www.facebook.com/TheMusicalHop",
               seeking_talent=True,
               image_link="https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
               seeking_description="We are on the lookout for a local artist to play every two weeks. Please call us.",
               )

    s1 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=1)).replace(microsecond=0))
    s2 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=2)).replace(microsecond=0))
    s3 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=-1)).replace(microsecond=0))
    s4 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=3)).replace(microsecond=0))
    s5 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=-3)).replace(microsecond=0))
    s6 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=1)).replace(microsecond=0))
    s7 = Show(start_time=(datetime.datetime.today() +
                          datetime.timedelta(days=4)).replace(microsecond=0))

    v1.city = c1
    v1.genres.extend((g1, g4))
    v2.city = c1
    v2.genres.extend((g2, g1, g3))
    v3.city = c2
    v3.genres.extend((g3, g1))
    v4.city = c1
    v4.genres.extend((g3, g1, g2))

    a1 = Artist(
        name="Guns N Petals",
        phone="01010101010",
        website="https://www.gunsnpetalsband.com",
        facebook_link="https://www.facebook.com/GunsNPetals",
        seeking_venue=True,
        seeking_description="Looking for shows to perform at in the San Francisco Bay Area!",
        image_link="https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    )

    a2 = Artist(
        name="Matt Quevado",
        phone="01010101010",
        website="https://www.gunsnpetalsband.com",
        facebook_link="https://www.facebook.com/GunsNPetals",
        seeking_venue=True,
        seeking_description="Looking for shows to perform at in the San Francisco Bay Area!",
        image_link="https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    )

    a3 = Artist(
        name="The Wild Sax Band",
        phone="01010101010",
        website="https://www.gunsnpetalsband.com",
        facebook_link="https://www.facebook.com/GunsNPetals",
        seeking_venue=True,
        seeking_description="Looking for shows to perform at in the San Francisco Bay Area!",
        image_link="https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    )

    a1.city = c1
    a1.genres.extend((g3, g1))
    a2.city = c2
    a2.genres.extend((g1, g4, g3))
    a3.city = c2
    a3.genres.extend((g2, g1))

    s1.artist = a2
    s1.venue = v1

    s2.artist = a1
    s2.venue = v3

    s3.artist = a3
    s3.venue = v1

    s4.artist = a3
    s4.venue = v2

    s5.artist = a3
    s5.venue = v2

    s6.artist = a1
    s6.venue = v3

    s7.artist = a3
    s7.venue = v4

    db.session.add(c1)
    db.session.add(c2)

    db.session.add(g1)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)

    db.session.add(v1)
    db.session.add(v2)
    db.session.add(v3)

    db.session.add(a1)
    db.session.add(a2)
    db.session.add(a3)

    db.session.add(s1)
    db.session.add(s2)
    db.session.add(s3)

    db.session.commit()


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
