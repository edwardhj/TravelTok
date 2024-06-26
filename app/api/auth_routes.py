from flask import Blueprint, request, jsonify
from app.models import User, db, Follow
from app.forms import LoginForm
from app.forms import SignUpForm
from app.forms import EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.api.aws import upload_file_to_s3, get_unique_filename, remove_file_from_s3

auth_routes = Blueprint('auth', __name__)


@auth_routes.route('/')
def authenticate():
    """
    Authenticates a user.
    """
    if current_user.is_authenticated:
        user_dict = current_user.to_dict()

        follower_count = db.session.query(Follow).filter(Follow.c.following_user_id == current_user.id).count()
        following_count = db.session.query(Follow).filter(Follow.c.follower_user_id == current_user.id).count()
    
        user_dict['followers_count'] = follower_count
        user_dict['following_count'] = following_count

        return user_dict
    
    return {'message': "No user is logged in"}, 401

@auth_routes.route('/editprofile', methods=['PUT'])
@login_required
def edit_profile():
    """
    edits a user's profile
    """

    form = EditProfileForm(obj=current_user)

    form['csrf_token'].data = request.cookies['csrf_token']
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        if form.profile_pic.data:
            filename = get_unique_filename(form.profile_pic.data.filename)
            form.profile_pic.data.filename = filename
            upload = upload_file_to_s3(form.profile_pic.data)

            if "url" not in upload:
                return jsonify({"error": "File upload failed", "details": upload}), 400
            
            current_user.profile_pic = upload["url"]

        db.session.commit()
        return jsonify({"message": "Profile has been updated successfully"}), 200
    else:
        error_messages = {}
        for field, errors in form.errors.items():
            error_messages[field] = errors[0]

        response = jsonify({
            "message": "Bad Request",
            "error": error_messages,
        })
        response.status_code = 400
        return response


@auth_routes.route('/login', methods=['POST'])
def login():
    """
    Logs a user in
    """
    form = LoginForm()
    # Get the csrf_token from the request cookie and put it into the
    # form manually to validate_on_submit can be used
    form['csrf_token'].data = request.cookies['csrf_token']
    if form.validate_on_submit():
        # Add the user to the session, we are logged in!
        user = User.query.filter(User.email == form.data['email']).first()
        login_user(user)
        return user.to_dict()
    # if "email" in form.errors:
    #     if form.errors["email"][0] == "Email provided not found.":
    #         return jsonify({"error": "User associated with email not found"}), 401
    # if "password" in form.errors:
    #     if form.errors["password"][0] == "Password was incorrect.":
    #         return jsonify({"error": "Invalid password"}), 401
    return jsonify(form.errors), 401


@auth_routes.route('/logout')
def logout():
    """
    Logs a user out
    """
    logout_user()
    return {'message': 'User has been successfully logged out'}


@auth_routes.route('/signup', methods=['POST'])
def sign_up():
    """
    Creates a new user and logs them in
    """
    form = SignUpForm()

    form['csrf_token'].data = request.cookies['csrf_token']
    if form.validate_on_submit():
        first_name = form.data['first_name']
        last_name = form.data['last_name']
        username = form.data['username']
        email = form.data['email']
        password = form.data['password']
        profile_pic = form.data['profile_pic']

        if profile_pic:
            profile_pic.filename = get_unique_filename(profile_pic.filename)
            upload = upload_file_to_s3(profile_pic)

            if "url" not in upload:
            # if the dictionary doesn't have a url key
                return jsonify({"error": "File upload failed", "details": upload}), 400
            
            url = upload["url"]
        else:
            url = None

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            profile_pic=url
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return user.to_dict()
    # return form.errors, 401
    # if form.errors["email"][0] == "Email address is already in use.":
    #    return {"error": "Email already exists", "errors": form.errors}, 500
    else:
        return jsonify(form.errors), 400


@auth_routes.route('/unauthorized')
def unauthorized():
    """
    Returns unauthorized JSON when flask-login authentication fails
    """
    return {'errors': {'message': 'Forbidden'}}, 403