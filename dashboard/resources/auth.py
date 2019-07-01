from flask_restful import Resource, reqparse
from flask_security.utils import hash_password, verify_password
from flask_security.recoverable import reset_password_token_status
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)

from .. import user_datastore, jwt
from ..models import RevokedTokenModel
from ..myutils import send_reset_password_instructions, update_password

from datetime import datetime, timedelta

parser = reqparse.RequestParser()
parser.add_argument('email', help = 'This field cannot be blank')
parser.add_argument('password')
parser.add_argument('username')
parser.add_argument('tg_address')
parser.add_argument('token')


class UserRegistration(Resource):
    def post(self):
        data = parser.parse_args()
        if user_datastore.get_user(data['email']):
            print ("Email already taken")
            return {'message': f'Email {data["email"]} exists', 'registered':False}, 401
        new_user = user_datastore.create_user(email = data['email'], password=hash_password(data['password']), username=data['username'])
        try:
            new_user.save_to_db()
            access_token = create_access_token(identity=data['email'])
            refresh_token = create_refresh_token(identity=data['email'])
        except Exception as e:
            return {
                       'error': str(e)
                   }, 500
        return {
            "registered": True,
            "email" : new_user.email,
            "avatar": new_user.avatar,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            },
            "message": "User Registration is successful",
            "user": new_user.serialize()
        }

class UserLogin(Resource):
    def post(self):
        data = parser.parse_args()
        current_user = user_datastore.get_user(data['email'])
        if not current_user:
            return {'message': 'Incorrect Email or password',
                    "loggedIn": False}, 401

        if verify_password(data['password'], current_user.password):
            access_token = create_access_token(identity=data['email'])
            refresh_token = create_refresh_token(identity=data['email'])
            user = user_datastore.get_user(data['email'])
            return {
                'message': 'Successfully logged in as {}'.format(current_user.email),
                "tokens" : {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                },
                "loggedIn":True,
                "user" : user.serialize()
            }
        else:
            return {'message': 'Incorrect Email or password',
                    "loggedIn": False}, 401


class UserOAuthLogin(Resource):
    def post(self):
        data = parser.parse_args()

        print(f"Our data is {data}")
        email = data['email']
        social_id = data['social_id']
        username = data['username']
        avatar_url = data['avatar_url']
        social_type = data['type']

        if not email or not social_id:
            return {'message': 'We could not get your email or social ID',
                    "loggedIn": False}, 401

        current_user = user_datastore.get_user(data['email'])
        if current_user: #email address stored
            if current_user.social_id: #user has a social_id
                if current_user.social_id == social_id: #user is good to go
                    access_token = create_access_token(identity=email)
                    refresh_token = create_refresh_token(identity=email)

                else:
                    return {'message': f'Incorrect {social_type} ID for user {username}',
                            "loggedIn": False}, 401

            else: #we have to compromise here, user has email saved, is trying to go social, but we have not saved the social ID
                current_user.social_id = social_id
                current_user.username = username
                current_user.social_type = social_type

                access_token = create_access_token(identity=email)
                refresh_token = create_refresh_token(identity=email)

            if not current_user.username and username:
                current_user.username = username
            if not current_user.avatar and avatar_url:
                current_user.avatar = avatar_url

            current_user.save_to_db()
            return {
                'message': 'Successfully logged in as {}'.format(current_user.email),
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                },
                "loggedIn": True,
                "user": current_user.serialize()
            }

        else:
            new_user = user_datastore.create_user(email=email, social_id=social_id, avatar=avatar_url, username=username, social_type=social_type )
            try:
                new_user.save_to_db()
                access_token = create_access_token(identity=data['email'])
                refresh_token = create_refresh_token(identity=data['email'])
            except Exception as e:
                return {'error': str(e)}, 500
            return {
                "registered": True,
                "email": new_user.email,
                "avatar": new_user.avatar,
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                },
                "message": "User Registration is successful",
                "user": new_user.serialize()
            }

class UserLogoutAccess(Resource):

    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500

class UserLogoutRefresh(Resource):

    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500

class TokenRefresh(Resource):

    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        print("Our current user is", current_user)
        access_token = create_access_token(identity=current_user)
        return {'access_token': access_token, "expires_at" : (datetime.utcnow() + timedelta(minutes=15)).isoformat()}

class SendPasswordResetEmail(Resource):

    def post(self):
        data = parser.parse_args()
        if not data['email']:
            return {'message': 'Provide Email',
                    "loggedIn": False}, 401
        current_user = user_datastore.get_user(data['email'])
        if not current_user:
            return {'message': 'Email was not found',
             "loggedIn": False}, 401
        send_reset_password_instructions(current_user)
        return {'message': 'An email has been sent with instructions to reset password'}

class ResetPassword(Resource):

    def post(self):
        data = parser.parse_args()
        print("We are here")
        if not data['password'] or not data['token']:
            return {'message': 'Provide Password and the token sent',
                    "loggedIn": False}, 401
        expired, invalid, user = reset_password_token_status(data['token'])
        if expired:
            return {'message': 'The password reset token provided has expired',
                    "loggedIn": False}, 401
        if invalid:
            return {'message': 'Invalid token provided',
                    "loggedIn": False}, 401
        if not user:
            return {'message': 'Could not find a user for that account',
                    "loggedIn": False}, 401
        print("Updating password for", user.username)
        update_password(user, data['password'])
        return {'message': 'The password for your account has been successfully updated'}


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)