import os
import time

from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, logout_user, login_required, current_user, login_user
import boto3
import io

from PIL import Image, ExifTags

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY")
S3_SECRET = os.environ.get("S3_SECRET_ACCESS_KEY")

from models import Trip, Adventure, Location, Photo, User


s3_resource = boto3.resource(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

s3_client = boto3.client('s3',
                         aws_access_key_id=S3_KEY,
                         aws_secret_access_key=S3_SECRET)

bucket = s3_resource.Bucket('trip-blog')

def download_image(s3, resource):
    """ resource: name of the file to download"""
    url = s3.generate_presigned_url('get_object',
                                    Params = {'Bucket': 'trip-blog',
                                    'Key': resource}, ExpiresIn = 100)
    return url

# @app.route("/")
# def hello():
#     return "Hello World!"

# @app.route("/trips/new")
# def new_trip():
#     name=request.args.get('name')
#     photo_url=request.args.get('photo_url')
#     published=request.args.get('published')
#     try:
#         trip=Trip(
#             name=name,
#             photo_url=photo_url,
#             published=published
#         )
#         db.session.add(trip)
#         db.session.commit()
#         return "Book added. book id={}".format(trip.id)
#     except Exception as e:
# 	    return(str(e))

@app.route("/trips/<id_>/adventures/new",methods=['GET', 'POST'])
def add_adventure_form(id_):
    if request.method == 'POST':
        name=request.form.get('name')
        summary=request.form.get('summary')
        trip_id=request.form.get('trip_id')
        published=request.form.get('published')
        try:
            adventure=Adventure(
                name=name,
                summary=summary,
                trip_id=trip_id,
                published=published
            )
            db.session.add(adventure)
            db.session.commit()
            return redirect(f'/trips/{id_}/adventures/{adventure.id}/locations/new')
        except Exception as e:
            return(str(e))
    return render_template("adventures/new.html", trip_id=id_)

@app.route("/trips/<id_>/adventures/<ida_>/locations/new",methods=['GET', 'POST'])
def add_location_form(id_, ida_):
    if request.method == 'POST':
        name=request.form.get('name')
        summary=request.form.get('summary')
        adventure_id=request.form.get('adventure_id')
        visit_time=request.form.get('visit_time')
        try:
            location=Location(
                name=name,
                summary=summary,
                adventure_id=adventure_id,
                visit_time=visit_time
            )
            db.session.add(location)
            db.session.commit()
            location = Location.query.order_by(Location.id.desc()).first()
            location = location.__dict__
            return redirect(f'/trips/{id_}/adventures/{ida_}/locations/{location["id"]}/photos/new')
        except Exception as e:
            return(str(e))
    return render_template("locations/new.html", adventure_id=ida_)

def photo_to_db(photo_url, subtitle, location_id):
    try:
        photo=Photo(
            photo_url=photo_url,
            subtitle=subtitle,
            location_id=location_id
        )
        db.session.add(photo)
        db.session.commit()
        return "Photo added. Photo id={}".format(photo.id)
    except Exception as e:
        return(str(e))

def photo_to_s3(in_mem_file, photo_url):
    try:
        s3_client.upload_fileobj(
        in_mem_file,
        'trip-blog',
        photo_url
        )
    except Exception as e:
        return (str(e))

def upload_photo(request, id_, ida_, idl_, edit=False):
    subtitle=request.form.get('subtitle')
    location_id=request.form.get('location_id')
    user_file=request.files["user_file"]
    photo_url = name_photo(user_file, request.form.get('photo_url'), id_, ida_, idl_)

    image=Image.open(user_file)
    format = image.format
    in_mem_file = io.BytesIO()
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation]=='Orientation':
            break
    if image._getexif() is not None:
        exif=dict(image._getexif().items())

        if exif[orientation] == 3:
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image=image.rotate(90, expand=True)

    image.save(in_mem_file, format=format)
    in_mem_file.seek(0)
    photo_to_s3(in_mem_file, photo_url)
    if not edit:
        photo_to_db(photo_url, subtitle, location_id)
        return redirect(f'/trips/{id_}/adventures/{ida_}/locations/{idl_}')

    return photo_url

def name_photo(user_file, photo_url, id_, ida_, idl_):
    photo_url = f'trips/{id_}/adventures/{ida_}/locations/{idl_}/{photo_url}_{int(time.time())}'
    if user_file.mimetype == 'image/png':
        photo_url += '.png'
    elif user_file.mimetype == 'image/jpeg':
        photo_url += '.jpg'

    return photo_url

@app.route("/trips/<id_>/adventures/<ida_>/locations/<idl_>/photos/new",methods=['GET', 'POST'])
def add_photo_form(id_, ida_, idl_):
    location = Location.query.filter_by(id=idl_).first()
    location = location.__dict__
    if request.method == 'POST':
        photo_url = upload_photo(request, id_, ida_, idl_)

    return render_template("photos/new.html", trip_id=id_, adventure_id=ida_,
                           location_id=idl_, location_name=location['name'])

def delete_photo(photo_url):
    s3_resource.Object('trip-blog', photo_url).delete()


@app.route("/trips/<id_>/adventures/<ida_>/locations/<idl_>/photos/<idp_>/edit", methods=['GET', 'POST'])
def edit_photo_form(id_, ida_, idl_, idp_):
    if request.method == 'POST':
        photo_url=request.form.get('photo_url')
        subtitle=request.form.get('subtitle')
        user_file = request.files['user_file']
        user_file.seek(0, os.SEEK_END)
        file_attached = True
        if user_file.tell() == 0:
            file_attached = False
        photo=Photo.query.filter_by(id=idp_).first()
        if file_attached:
            photo_url = upload_photo(request, id_, ida_, idl_)
            delete_photo(photo.photo_url)
            photo.photo_url=photo_url
            photo.subtitle=subtitle
            db.session.commit()
            return "Photo modified. photo id={}".format(photo.id)
        else:
            photo.subtitle=subtitle
            db.session.commit()
            return "Photo modified just summery. photo id={}".format(photo.id)
    else:
        try:
            photo=Photo.query.filter_by(id=idp_).first()
            photo = photo.__dict__#[x.serialize() for x in trip]
            return render_template("photos/edit.html", photo=photo)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
        except Exception as e:
    	    return(str(e))

    return render_template("locations/new.html")

@app.route("/trips/new",methods=['GET', 'POST'])
def add_trip_form():
    if request.method == 'POST':
        name=request.form.get('name')
        photo_url=request.form.get('photo_url')
        published=request.form.get('published')
        try:
            trip=Trip(
                name=name,
                photo_url=photo_url,
                published=published
            )
            db.session.add(trip)
            db.session.commit()
            return "Trip added. trip id={}".format(trip.id)
        except Exception as e:
            return(str(e))
    return render_template("trips/new.html")

@app.route("/trips/<id_>/edit", methods=['GET', 'POST'])
def edit_trip_form(id_):
    if request.method == 'POST':
        name=request.form.get('name')
        published=request.form.get('published')
        trip=Trip.query.filter_by(id=id_).first()
        try:
            trip.name=name
            trip.published=published
            db.session.commit()
            return "Trip modified. trip id={}".format(trip.id)
        except Exception as e:
            return(str(e))
    else:
        try:
            trip=Trip.query.filter_by(id=id_).first()
            trip = trip.__dict__#[x.serialize() for x in trip]
            if trip['photo_url']:
                trip['photo_url'] = download_image(s3_client, trip['photo_url'])
            return render_template("trips/edit.html", trip=trip)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
        except Exception as e:
    	    return(str(e))

    return render_template("trips/new.html")

@app.route("/trips")
def trips_redirect():
    return get_all()

@app.route("/")
def get_all():
    try:
        trips=Trip.query.order_by(Trip.published.desc(), Trip.id.desc()).all()
        trips = [x.serialize() for x in trips]
        for ix, trip in enumerate(trips):
            if trips[ix]['photo_url']:
                trips[ix]['photo_url'] = download_image(s3_client, trips[ix]['photo_url'])
        return render_template("trips/index.html", trips=trips, current_user=current_user)
    except Exception as e:
	    return(str(e))

    # return render_template("trips/index.html", trips=trip, photos=photos)

@app.route("/trips/<id_>")
def get_by_id(id_):
    try:
        trip=Trip.query.filter_by(id=id_).first()
        trip = trip.__dict__#[x.serialize() for x in trip]
        if trip['photo_url']:
            trip['photo_url'] = download_image(s3_client, trip['photo_url'])
        adventures=Adventure.query.filter_by(trip_id=id_).order_by(Adventure.published.asc()).all()
        adventures = [x.serialize() for x in adventures]
        return render_template("trips/show.html", trip=trip, adventures=adventures)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
    except Exception as e:
	    return(str(e))

@app.route("/trips/<id_>/adventures/<ida_>/edit", methods=['GET', 'POST'])
def edit_adventure_form(id_, ida_):
    if request.method == 'POST':
        name=request.form.get('name')
        summary=request.form.get('summary')
        published=request.form.get('published')
        adventure=Adventure.query.filter_by(id=ida_).first()
        try:
            adventure.name=name
            adventure.published=published
            adventure.summary=summary
            db.session.commit()
            return redirect(f'/trips/{id_}/adventures/{adventure.id}')
        except Exception as e:
            return(str(e))
    else:
        try:
            adventure=Adventure.query.filter_by(id=ida_).first()
            adventure = adventure.__dict__#[x.serialize() for x in trip]
            return render_template("adventures/edit.html", trip=id_, adventure=adventure)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
        except Exception as e:
    	    return(str(e))

    return render_template("adventures/new.html")


@app.route("/trips/<id_>/adventures/<ida_>/locations/<idl_>/edit", methods=['GET', 'POST'])
def edit_location_form(id_, ida_, idl_):
    if request.method == 'POST':
        name=request.form.get('name')
        summary=request.form.get('summary')
        visit_time=request.form.get('visit_time')
        location=Location.query.filter_by(id=idl_).first()
        try:
            location.name=name
            location.visit_time=visit_time
            location.summary=summary
            db.session.commit()
            return redirect(f'/trips/{id_}/adventures/{ida_}')
        except Exception as e:
            return(str(e))
    else:
        try:
            location=Location.query.filter_by(id=idl_).first()
            location = location.__dict__#[x.serialize() for x in trip]
            return render_template("locations/edit.html", trip=id_, location=location)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
        except Exception as e:
    	    return(str(e))

    return render_template("locations/new.html")


@app.route("/trips/<id_>/adventures/<ida_>")
def get_adventure(id_, ida_):
    try:
        trip=Trip.query.filter_by(id=id_).first()
        trip = trip.__dict__
        adventure=Adventure.query.filter_by(id=ida_).first()
        adventure=adventure.__dict__
        locations=(Location.query
                           .filter_by(adventure_id=ida_)
                           .order_by(Location.visit_time.asc()))
        locations = [x.serialize() for x in locations]
        photos = (db.session.query(Photo)
                            .join(Location, Photo.location_id==Location.id)
                            .all())
        photos = [x.serialize() for x in photos]
        loc_photos = {}
        for photo in photos:
            loc_photos.setdefault(photo['location_id'], {'subtitles': [],
                                                         'photo_urls': [],
                                                         'photo_ids': []})
            loc_photos[photo['location_id']]['subtitles'].append(photo['subtitle'])
            loc_photos[photo['location_id']]['photo_ids'].append(photo['id'])
            photo_url = download_image(s3_client, photo['photo_url'])
            loc_photos[photo['location_id']]['photo_urls'].append(photo_url)

        for ix, location in enumerate(locations):
            locations[ix]['photos'] = []
            if location['id'] in loc_photos:
                for subtitle, photo_url, photo_id in zip(loc_photos[location['id']]['subtitles'],
                                                         loc_photos[location['id']]['photo_urls'],
                                                         loc_photos[location['id']]['photo_ids']):
                    locations[ix]['photos'].append({'subtitle': subtitle,
                                                    'photo_url': photo_url,
                                                    'photo_id': photo_id})
        return render_template("adventures/show.html", trip_id=id_, trip=trip, adventure=adventure, locations=locations, photos=loc_photos)#jsonify(trip.serialize())#, jsonify([e.serialize() for e in adventure])
    except Exception as e:
	    return(str(e))

@app.route('/admin/users/logout')
def logout():
    logout_user()
    return redirect('/trips')


@app.route("/admin/users/new",methods=['GET', 'POST'])
def add_user_form():
    if request.method == 'POST':
        user_name=request.form.get('user_name')
        password=request.form.get('password')
        try:
            user=User(
                user_name=user_name,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            return "User added. user id={}".format(user.id)
        except Exception as e:
            return(str(e))
    return render_template("/admin/users/new.html")


@app.route("/admin/users/login",methods=['GET', 'POST'])
def user_login_form():
    if request.method == 'POST':
        user_name=request.form.get('user_name')
        password=request.form.get('password')
        user = User.query.filter_by(user_name=user_name).first()
        if user is None or not user.check_password(password):
            return 'wrong'
        else:
            login_user(user)
            return redirect('/admin')
    return render_template("/admin/users/new.html")
