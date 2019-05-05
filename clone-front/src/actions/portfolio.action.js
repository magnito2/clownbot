import { portfoliosConstants } from '../constants';
import { portfoliosService } from "../services";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const portfoliosActions = {
    get,
    getBTCValues
};

function get(id) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => portfoliosService.get(id))
            .then(
                portfolio => dispatch(success(portfolio)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: portfoliosConstants.GET_REQUEST } }
    function success(portfolio) { return { type: portfoliosConstants.GET_SUCCESS, portfolio } }
    function failure(error) { return { type: portfoliosConstants.GET_FAILURE, error } }
}

function getBTCValues() {
    return dispatch => {
        dispatch(request());

        authorize().then(() => portfoliosService.getBTCValues())
            .then(
                btc_values => dispatch(success(btc_values)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: portfoliosConstants.GET_BTC_REQUEST } }
    function success(portfolio) { return { type: portfoliosConstants.GET_BTC_SUCCESS, portfolio } }
    function failure(error) { return { type: portfoliosConstants.GET_BTC_FAILURE, error } }
}