import { userConstants } from '../constants';
import { userService } from "../services/user.service";
import { alertActions } from './';
import { history } from '../helpers';

export const userActions = {
    login,
    logout,
    register,
    getAll,
    delete: _delete,
    oauthlogin,
    password_reset_request,
    reset_password
};

function login(username, password) {
    return dispatch => {
        dispatch(request({ username }));

        userService.login(username, password)
            .then(
                user => {
                    dispatch(success(user));
                    history.push('/');
                    dispatch(alertActions.success(user.message.toString()));
                    console.log("login successful");
                },
                error => {
                    console.log("login failed", error.toString());
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(user) { return { type: userConstants.LOGIN_REQUEST, user } }
    function success(user) { return { type: userConstants.LOGIN_SUCCESS, user } }
    function failure(error) { return { type: userConstants.LOGIN_FAILURE, error } }
}

function oauthlogin(data) {
    return dispatch => {
        console.log(data);
        dispatch(request({ username : data.username }));

        userService.oauthlogin(data)
            .then(
                user => {
                    dispatch(success(user));
                    history.push('/');
                    dispatch(alertActions.success('Login successful'));
                    dispatch(alertActions.success(user.message.toString()));
                    console.log("login successful");
                },
                error => {
                    console.log("logging failed", error.toString());
                    console.log(error);
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(user) { return { type: userConstants.LOGIN_REQUEST, user } }
    function success(user) { return { type: userConstants.LOGIN_SUCCESS, user } }
    function failure(error) { return { type: userConstants.LOGIN_FAILURE, error } }
}

function logout() {
    userService.logout();
    history.push('/login');
    alertActions.success('Bye! See you next time');
    return { type: userConstants.LOGOUT };
}

function register(user) {
    return dispatch => {
        dispatch(request(user));

        userService.register(user)
            .then(
                user => {
                    dispatch(success(user));
                    history.push('/');
                    dispatch(alertActions.success('Registration successful'));
                },
                error => {
                    console.log("Registration failed,", error.toString());
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(user) { return { type: userConstants.REGISTER_REQUEST, user } }
    function success(user) { return { type: userConstants.REGISTER_SUCCESS, user } }
    function failure(error) { return { type: userConstants.REGISTER_FAILURE, error } }
}

function getAll() {
    return dispatch => {
        dispatch(request());

        userService.getAll()
            .then(
                users => dispatch(success(users)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: userConstants.GETALL_REQUEST } }
    function success(users) { return { type: userConstants.GETALL_SUCCESS, users } }
    function failure(error) { return { type: userConstants.GETALL_FAILURE, error } }
}

// prefixed function name with underscore because delete is a reserved word in javascript
function _delete(id) {
    return dispatch => {
        dispatch(request(id));

        userService.delete(id)
            .then(
                user => dispatch(success(id)),
                error => dispatch(failure(id, error.toString()))
            );
    };

    function request(id) { return { type: userConstants.DELETE_REQUEST, id } }
    function success(id) { return { type: userConstants.DELETE_SUCCESS, id } }
    function failure(id, error) { return { type: userConstants.DELETE_FAILURE, id, error } }
}

function password_reset_request(email) {
    return dispatch => {
        dispatch(request(email));

        userService.password_reset_request(email)
            .then( () => {
                    dispatch(success());
                    dispatch(alertActions.success('Check your email on instructions to reset your password'));
                    setTimeout(function(){ history.push("/") }, 3000);
                },
                error => {
                    console.log("Send Email Failed,", error.toString());
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(email) { return { type: userConstants.SEND_PASSWORD_RESET_EMAIL_REQUEST, email } }
    function success() { return { type: userConstants.SEND_PASSWORD_RESET_EMAIL_SUCCESS } }
    function failure(error) { return { type: userConstants.SEND_PASSWORD_RESET_EMAIL_FAILURE, error } }
}

function reset_password(password, token) {
    return dispatch => {
        dispatch(request());
        console.log('pass: ',password, 'token: ', token);
        userService.reset_password(password, token)
            .then( () => {
                    dispatch(success());
                    dispatch(alertActions.success('Password has been reset successfully'));
                    setTimeout(function(){ history.push("/") }, 3000);
                },
                error => {
                    console.log("Password Reset Failed,", error);
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request() { return { type: userConstants.RESET_PASSWORD_REQUEST } }
    function success() { return { type: userConstants.RESET_PASSWORD_SUCCESS } }
    function failure(error) { return { type: userConstants.RESET_PASSWORD_FAILURE, error } }
}