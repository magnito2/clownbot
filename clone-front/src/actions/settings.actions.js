import { settingsConstants } from '../constants';
import { settingsService } from "../services/settings.service";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const settingsActions = {
    create,
    update,
    get,
    createAvatar,
};

function create(settings) {
    return dispatch => {
        dispatch(request({ settings }));

        authorize().then(() => settingsService.create(settings))
            .then(
                settings => {
                    console.log("Success creating settings");
                    dispatch(success(settings));
                    dispatch(alertActions.success('New Settings created'));
                    //dispatch(alertActions.success(settings.message.toString()));
                    console.log("settings created", settings);
                },
                error => {
                    console.log("creating settings failed", error);
                    dispatch(failure(error));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(settings) { return { type: settingsConstants.CREATE_REQUEST, settings } }
    function success(settings) { return { type: settingsConstants.CREATE_SUCCESS, settings } }
    function failure(error) { return { type: settingsConstants.CREATE_FAILURE, error } }
}

function update(settings) {
    return dispatch => {
        dispatch(request(settings));
        console.log("We have dispatched settings request");
        authorize().then(() => settingsService.update(settings))
            .then(
                settings => {
                    dispatch(success(settings));
                    dispatch(alertActions.success('Settings has been updated'));
                },
                error => {
                    console.log("Failed to update settings", error.toString());
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(settings) { return { type: settingsConstants.UPDATE_REQUEST, settings } }
    function success(settings) { return { type: settingsConstants.UPDATE_SUCCESS, settings } }
    function failure(error) { return { type: settingsConstants.UPDATE_FAILURE, error } }
}

function get() {
    return dispatch => {
        dispatch(request());

        authorize().then(() => settingsService.get())
            .then(
                settings => {
                    dispatch(success(settings));
                    console.log("We have recieved the following settings", settings);
                },
                error => dispatch(failure(error.toString()))

            );
    };

    function request() { return { type: settingsConstants.GET_REQUEST } }
    function success(settings) { return { type: settingsConstants.GET_SUCCESS, settings } }
    function failure(error) { return { type: settingsConstants.GET_FAILURE, error } }
}

function updateField(field) {
    return dispatch => {
        dispatch(request(field));

        authorize().then(() => settingsService.update(field))
            .then(
                user => {
                    dispatch(success(user));
                    dispatch(alertActions.success('User has been updated'));
                },
                error => {
                    console.log("Failed to update user", error.toString());
                    dispatch(failure(error.toString()));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(user) { return { type: settingsConstants.UPDATE_REQUEST, user } }
    function success(user) { return { type: settingsConstants.UPDATE_SUCCESS, user } }
    function failure(error) { return { type: settingsConstants.UPDATE_FAILURE, error } }
}

function createAvatar(avatar) {
    return dispatch => {
        dispatch(request());

        authorize().then( () => settingsService.createAvatar(avatar))
            .then(
                settings => dispatch(success(settings)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: settingsConstants.CREATE_AVATAR_REQUEST } }
    function success(settings) { return { type: settingsConstants.CREATE_AVATAR_SUCCESS, settings } }
    function failure(error) { return { type: settingsConstants.CREATE_AVATAR_FAILURE, error } }
}