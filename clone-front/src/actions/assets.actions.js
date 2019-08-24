import { assetsConstants } from '../constants';
import { assetsService } from "../services";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const assetsActions = {
    getById,
    getAll,
};

function getById(id) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => assetsService.get(id))
            .then(
                asset => dispatch(success(asset)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: assetsConstants.GET_REQUEST } }
    function success(asset) { return { type: assetsConstants.GET_SUCCESS, asset } }
    function failure(error) { return { type: assetsConstants.GET_FAILURE, error } }
}

function getAll() {
    return dispatch => {
        dispatch(request());

        authorize().then(() => assetsService.get())
            .then(
                assets => dispatch(success(assets)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: assetsConstants.GETALL_REQUEST } }
    function success(assets) { return { type: assetsConstants.GETALL_SUCCESS, assets } }
    function failure(error) { return { type: assetsConstants.GETALL_FAILURE, error } }
}