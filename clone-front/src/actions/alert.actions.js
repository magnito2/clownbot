import {createNotification, NOTIFICATION_TYPE_SUCCESS, NOTIFICATION_TYPE_ERROR} from 'react-redux-notify';

export const alertActions = {
    success,
    error
};

function success(message) {
    return dispatch => dispatch(
        createNotification({
            type: NOTIFICATION_TYPE_SUCCESS,
            message,
            canDismiss: true,
            duration: 10000,
        }));
}

function error(message) {
    return dispatch => dispatch(
        createNotification({
            type: NOTIFICATION_TYPE_ERROR,
            message,
            canDismiss: true,
            duration: 10000,
        }));
}