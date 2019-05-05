import { signalsConstants } from '../constants';
import { signalsService } from "../services/signals.service";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const signalsActions = {
    create,
    get,
    getCheckedSignals
};

function create(signals) {
    return dispatch => {
        dispatch(request({ signals }));

        authorize().then(() => signalsService.create(signals))
            .then(
                signals => {
                    console.log("Success creating signals");
                    dispatch(success(signals));
                    dispatch(alertActions.success('New Signals created'));
                    //dispatch(alertActions.success(signals.message.toString()));
                    console.log("signals created", signals);
                },
                error => {
                    console.log("creating signals failed", error);
                    dispatch(failure(error));
                    dispatch(alertActions.error(error.toString()));
                }
            );
    };

    function request(signals) { return { type: signalsConstants.CREATE_REQUEST, signals } }
    function success(signals) { return { type: signalsConstants.CREATE_SUCCESS, signals } }
    function failure(error) { return { type: signalsConstants.CREATE_FAILURE, error } }
}

function get(exchange_account = null) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => signalsService.get(exchange_account))
            .then(
                signals => dispatch(success(signals)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: signalsConstants.GET_REQUEST } }
    function success(signals) { return { type: signalsConstants.GET_SUCCESS, signals } }
    function failure(error) { return { type: signalsConstants.GET_FAILURE, error } }
}

function getCheckedSignals(exchange_account) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => signalsService.getCheckedSignals(exchange_account))
            .then(
                signals => dispatch(success(signals)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: signalsConstants.GET_CHECKED_REQUEST } }
    function success(signals) { return { type: signalsConstants.GET_CHECKED_SUCCESS, signals } }
    function failure(error) { return { type: signalsConstants.GET_CHECKED_FAILURE, error } }
}