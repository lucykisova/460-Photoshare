######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'He$loSQL1'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email = request.form.get('email')
		password = request.form.get('password')
		fname = request.form.get('fname')
		lname = request.form.get('lname')
		gender = request.form.get('gender')
		hometown = request.form.get('hometown')
		dob = request.form.get('dob')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, gender, dob, hometown, fname, lname) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, gender, dob, hometown, fname, lname)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		return "<a href = '/login'>Try again</a></br> <a href = '/register'>or make an account</a>"


@app.route('/addfriend', methods=['GET'])
@flask_login.login_required
def addFriend():
	return render_template("/addfriend.html")

@app.route('/addfriend', methods=['POST'])
@flask_login.login_required
def addingFriend():

    print("GOT HERE")
    uid = getUserIdFromEmail(flask_login.current_user.id)
    print("uid: ", uid)

    friend_email = request.form.get('friend_email')
    friend_id = getUserIdFromEmail(friend_email)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Friendship(UID1,UID2) VALUES ('{0}', '{1}')".format(uid, friend_id))
    conn.commit()
    return render_template('hello.html', message='Congrats! You have added a new friend!')


@app.route('/friendslist', methods=['GET'])
@flask_login.login_required
def displayFriendsList():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT fname, lname FROM Users WHERE user_id IN (SELECT UID2 FROM Friendship WHERE UID1 = '{0}')".format(uid))
    data=cursor.fetchall()
    return render_template("/friendslist.html", message="Here are your friends!", friends=data)

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption, user_id FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]


def getPhotosFromAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption, user_id FROM Photos WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall()

@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        album_name = request.form.get('album_name')
        cursor.execute("INSERT INTO Albums (Name, user_id) VALUES ('{0}', '{1}')".format(album_name, uid))
        conn.commit()
        return render_template('createalbum.html', message = "Album created!")
    else:
        return render_template('createalbum.html')
    
# helper function deletes a photo
def DeleteHelperFunc(photo_id):
   cursor = conn.cursor()
   cursor.execute("DELETE FROM Tagged WHERE photo_id = '{0}'".format(photo_id))
   cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(photo_id))
   conn.commit()


# Deleting an photo
@app.route('/photoslist', methods=['GET', 'POST'])
@flask_login.login_required
def DeletePhotos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        photo_id = request.form.get('photo_id')
        DeleteHelperFunc(photo_id)
        return render_template('photoslist.html', message="Photo deleted! Here are your Photos.", photos=getUsersPhotos(uid), base64=base64)
    else:
        return render_template('photoslist.html', message="Here are your Photos.", photos=getUsersPhotos(uid), base64=base64)


@app.route('/deletealbum', methods=['GET', 'POST'])
@flask_login.login_required
def deleteAlbum():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        album_name = request.form.get('album_name')
        album_id = getAlbumIdFromName(album_name)
        cursor = conn.cursor()
        cursor.execute("SELECT photo_id FROM Photos WHERE album_id = '{0}'".format(album_id))
        photosAll = cursor.fetchall()
        for m in range(len(photosAll)):
            temp = int(photosAll[m][0])
            DeleteHelperFunc(temp)
        cursor.execute("DELETE FROM Albums WHERE user_id = '{0}' AND album_id = '{1}'".format(uid, album_id))
        conn.commit()
        return render_template('deletealbum.html', message="Album deleted!")
    else:
        print("GOT HERE GET")
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
        albums = cursor.fetchall()
        return render_template('deletealbum.html', message="Here are your albums", albums=albums)

@app.route('/browsealbum', methods=['GET', 'POST'])
def BrowseAlbum():
    if request.method == 'POST':
        user = request.form.get('user_email')
        uid = getUserIdFromEmail(user)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
        albums = cursor.fetchall()
        return render_template('choosealbum.html', message='Here are their albums', albums=albums)
    else:
        return render_template('browsealbum.html')


# Start view photos
@app.route('/viewphotos', methods=['GET'])
def viewPhotos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM Albums WHERE user_id = '{0}'".format(uid))
    album_data = cursor.fetchall()
    return render_template('photoslist.html', message='Here are your photos', albums=album_data)


@app.route('/viewphotos/<album_name>', methods=['GET'])
def showPhotos(album_name):
    album_id = getAlbumIdFromName(album_name)
    photo_data = getPhotosFromAlbum(album_id)
    return render_template('photoslist.html', message='Here are your photos', photos=photo_data, base64=base64)


@app.route('/mostcontributedusers', methods=['GET'])
def mostContributedUsers():
    if request.method == 'POST':
        user_email = request.form.get('user_name')
        cursor = conn.cursor()
        cursor.execute("SELECT fname, lname FROM Users WHERE email = '{0}'".format(user_email))
        users = cursor.fetchall()
        return render_template('mostcontributedusers.html', message='Here are your photos containing this tag', users=users)
    else:
        return render_template("mostcontributedusers.html", users=topThreeUsers())
    

def topThreeUsers():
    cursor = conn.cursor()
    cursor.execute("SELECT email, fname, lname, COUNT(photo_id) FROM Users, Photos WHERE Photos.user_id = Users.user_id GROUP BY email ORDER BY COUNT(photo_id) DESC LIMIT 3")
    users = cursor.fetchall()
    return users

@app.route('/viewprofile/<uid>', methods=['GET'])
def viewprofile(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	albums = cursor.fetchall()
	return render_template('choosealbum.html', message='Here is your profile', albums=albums)


@app.route('/friendsrec', methods=['GET'])
def friendRecommendation():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT email, fname, lname FROM Users Where user_id IN (SELECT DISTINCT f2.UID2 FROM Friendship AS f1 JOIN Friendship AS f2 ON f1.UID2 = f2.UID1 WHERE f1.UID1 = '{0}' AND f2.UID2 != f1.UID1)".format(uid))
	friends = cursor.fetchall()
	return render_template('friendsrec.html', message='Here are your recommended friends', friends=friends)


@app.route('/user_tags', methods=['GET', 'POST'])
@flask_login.login_required
def user_tags():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    if request.method == 'POST':
        tag_name = request.form.get('tag_name')
        photos = getPhotosTag(tag_name)
        return render_template('user_tags.html', message='Here are your photos containing this tag', photos=photos, base64=base64)
    else:
        return render_template("user_tags.html", tags = getUserTags())
    
# Photo with tags


@app.route('/photos_with_tag', methods=['GET', 'POST'])
def PhotoByTag():
   if request.method == 'POST':
       tag = request.form.get('tag')
       photos = tagPhotos(tag)
       return render_template('photos_with_tag.html', message="Here are the photos with this tag!", photos=photos, base64=base64)
   else:
       return render_template('photos_with_tag.html')
   

def getPhotosTag(tags):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, name, caption, fname, lname FROM Users, Photos, Tags, Tagged WHERE Tags.tag_id = Tagged.tag_id AND Tagged.photo_id = Photos.photo_id AND Photos.user_id = Users.user_id AND Tags.name = '{0}'".format(tags))
    photos = cursor.fetchall()
    return photos

    
def tagPhotos(tag_name):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, name, caption, fname, lname FROM Photos, Users, Tagged, Tags WHERE Tags.name = '{0}' AND Tagged.tag_id = Tags.tag_id AND Tagged.photo_id = Photos.photo_id AND Photos.user_id = Users.user_id".format(tag_name))
    tagged_photos = cursor.fetchall()
    return tagged_photos


def getUserTags():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM Tags, Tagged, Photos WHERE Tags.tag_id = Tagged.tag_id AND Tagged.photo_id = Photos.photo_id AND Photos.user_id = '{0}'".format(uid))
    tags = cursor.fetchall()
    return tags


@app.route('/populartags', methods=['GET', 'POST'])
def popularTags():
    if request.method == 'POST':
        tag_name = request.form.get('tag_name')
        cursor = conn.cursor()
        cursor.execute("SELECT imgdata, name, caption, fname, lname FROM Photos, Users, Tagged, Tags WHERE Tags.name = '{0}' AND Tagged.tag_id = Tags.tag_id AND Tagged.photo_id = Photos.photo_id AND Photos.user_id = Users.user_id".format(tag_name))
        photos = cursor.fetchall()
        return render_template('photos_with_tag.html', message='Here are your photos containing this tag', photos=photos, base64=base64)
    else:
        return render_template("populartags.html", tags = topFiveTags())
    

@app.route('/searchpopulartags', methods=['GET', 'POST'])
def PopularTagsSearch():
    if request.method == 'POST':
        tag = request.form.get('tag')
        cursor = conn.cursor()
        cursor.execute("SELECT imgdata, name, caption, fname, lname FROM Users, Photos, Tags, Tagged WHERE Tags.tag_id = Tagged.tag_id AND Tagged.photo_id = Photos.photo_id AND Photos.user_id = Users.user_id AND Tags.name = '{0}'".format(tag))
        photos = cursor.fetchall()
        return render_template('searchpopulartags.html', message="The photos for this tag.", photos=photos, base64=base64)
    else:
        return render_template('photos_with_tag.html', tags=topFiveTags())


def topFiveTags():
    cursor = conn.cursor()
    cursor.execute("SELECT name, COUNT(name) FROM Tags, Tagged WHERE Tags.tag_id = Tagged.tag_id GROUP BY name ORDER BY COUNT(name) DESC LIMIT 5")
    tags = cursor.fetchall()
    return tags


def getTagId(tag):
    cursor = conn.cursor()
    cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(tag))
    return cursor.fetchone()[0]


@app.route('/addComment', methods=['GET', 'POST'])
@flask_login.login_required
def addComment():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        comment = request.form.get('comment')
        photo_id = request.form.get('photo_id')
        user_id = request.form.get('user_id')
        user_id = int(user_id)
        if user_id == uid:
            return render_template('photoslist.html', message="You can't comment on your own photo!", photos=getUsersPhotos(uid), base64=base64)
        else:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Comments (user_id, photo_id, text) VALUES ('{0}', '{1}', '{2}')".format(user_id, photo_id, comment))
            conn.commit()
            return render_template('photoslist.html', message="Comment added! Here are your Photos.", photos=getUsersPhotos(uid), base64=base64)
    else:
        return render_template('photoslist.html', message="Here are your Photos.", photos=getUsersPhotos(uid), base64=base64)


@app.route('/viewcomments/<photo_id>', methods=['GET'])
@flask_login.login_required
def viewcomments(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT text, user_id FROM Comments WHERE photo_id = '{0}'".format(photo_id))
    data = cursor.fetchall()
    cursor.execute("SELECT (SELECT COUNT(*) FROM Likes WHERE photo_id = '{0}') AS likecount".format(photo_id))
    likes = cursor.fetchone()[0]
    return render_template('viewcomments.html', data=data, likes=likes)


@app.route('/searchcomments', methods=['GET', 'POST'])
@flask_login.login_required
def searchcomments():
    if request.method == 'POST':
        comment = request.form.get('comment')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, text, COUNT(*) AS ccount FROM Comments WHERE text='{0}' GROUP BY user_id ORDER BY ccount DESC".format(comment))
        data = cursor.fetchall()
        return render_template('viewcomments.html', data=data, base64=base64)
    else:
        return render_template('searchcomments.html')


@app.route('/likePhoto', methods=['GET', 'POST'])
@flask_login.login_required
def likePhoto():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        photo_id = request.form.get('photo_id')
        photo_id = int(photo_id)
        cursor = conn.cursor()
        cursor.execute("SELECT photo_id FROM Likes WHERE user_id = '{0}' AND photo_id = '{1}'".format(uid, photo_id))
        likes = cursor.fetchall()
        for i in range (len(likes)):
            if likes[i][0] == photo_id:
                return render_template('photoslist.html', message="You already liked this photo!", photos=getUsersPhotos(uid), base64=base64)
        cursor.execute("INSERT INTO Likes (user_id, photo_id) VALUES ('{0}', '{1}')".format(uid, photo_id))
        conn.commit()
        return render_template('photoslist.html', message="Photo liked!", photos=getUsersPhotos(uid), base64=base64)
    else:
        return render_template('photoslist.html', message="Here are your Photos.", photos=getUsersPhotos(uid), base64=base64)
    
    
@app.route('/showLikes', methods=['GET', 'POST'])
def showLikes():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        uid = request.form.get('user_id')
        photo_id = request.form.get('photo_id')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(user_id) FROM Likes WHERE photo_id = '{0}'".format(photo_id))
        num_likes = cursor.fetchall()
        cursor.execute("SELECT fname, lname FROM Users, Likes WHERE Likes.user_id = Users.user_id AND Likes.photo_id = '{0}'".format(photo_id))
        users_liked = cursor.fetchall()
        return render_template('viewlikes.html', message="Here are the users who liked this photo", likes=num_likes, users=users_liked)
    else:
        return render_template('viewlikes.html')
    

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getAlbumIdFromName(album_name):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id FROM Albums WHERE Name = '{0}'".format(album_name))
    return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        photo_data = imgfile.read()
        album_name = request.form.get('album')
        album_id = getAlbumIdFromName(album_name)
        tag = request.form.get('tag')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Photos(imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s)", (photo_data, uid, caption, album_id))
        conn.commit()

        cursor.execute("SELECT photo_id FROM Photos WHERE imgdata = %s", (photo_data))
        photoid = cursor.fetchone()[0]

        # insert tags into database
        cursor.execute("INSERT INTO Tags(name) VALUES (%s)", (tag))

        tag_id = getTagId(tag)
        # Link tag and photo
        cursor.execute("INSERT INTO Tagged(photo_id, tag_id) VALUES (%s, %s)", (photoid, tag_id))
        conn.commit()
        return render_template('hello.html', message='Photo uploaded!')

    else:
        return render_template('upload.html', message='Photo uploaded!')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)

