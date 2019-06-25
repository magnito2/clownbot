import { tradesConstants } from '../constants';
import { tradesService } from "../services";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const tradesActions = {
    getById,
    getAll,

};

function getById(id) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => tradesService.get(id))
            .then(
                trade => dispatch(success(trade)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: tradesConstants.GET_REQUEST } }
    function success(trade) { return { type: tradesConstants.GET_SUCCESS, trade } }
    function failure(error) { return { type: tradesConstants.GET_FAILURE, error } }
}

function getAll() {
    return dispatch => {
        dispatch(request());

        authorize().then(() => tradesService.get())
            .then(
                trades => dispatch(success(trades)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: tradesConstants.GETALL_REQUEST } }
    function success(trades) { return { type: tradesConstants.GETALL_SUCCESS, trades } }
    function failure(error) { return { type: tradesConstants.GETALL_FAILURE, error } }
}