import { manualordersConstants } from '../constants';
import { manualordersService } from "../services";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const manualordersActions = {
    create,
    get,
    getSymbols
};

function create(manualorders) {
    return dispatch => {
        dispatch(request({ manualorders }));

        authorize().then(() => manualordersService.create(manualorders))
            .then(
                manualorders => {
                    console.log("Success creating manualorders");
                    dispatch(success(manualorders));
                    dispatch(alertActions.success('New Manualorders created'));
                    //dispatch(alertActions.success(manualorders.message.toString()));
                    console.log("manualorders created", manualorders);
                },
                error => {
                    console.log("creating manualorders failed", error);
                    dispatch(failure(error));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(manualorders) { return { type: manualordersConstants.CREATE_REQUEST, manualorders } }
    function success(manualorders) { return { type: manualordersConstants.CREATE_SUCCESS, manualorders } }
    function failure(error) { return { type: manualordersConstants.CREATE_FAILURE, error } }
}

function get(exchange_account = null) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => manualordersService.get(exchange_account))
            .then(
                manualorders => dispatch(success(manualorders)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: manualordersConstants.GET_REQUEST } }
    function success(manualorders) { return { type: manualordersConstants.GET_SUCCESS, manualorders } }
    function failure(error) { return { type: manualordersConstants.GET_FAILURE, error } }
}

function getSymbols(exchange) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => manualordersService.getSymbols(exchange))
            .then(
                symbols => dispatch(success(symbols)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: manualordersConstants.GET_SYMBOLS_REQUEST } }
    function success(symbols) { return { type: manualordersConstants.GET_SYMBOLS_SUCCESS, symbols } }
    function failure(error) { return { type: manualordersConstants.GET_SYMBOLS_FAILURE, error } }
}