import { ordersConstants } from '../constants';
import { ordersService } from "../services";
import { alertActions } from './';
import { history } from '../helpers';
import {authorize} from "../helpers/authorize";

export const ordersActions = {
    getById,
    getAll,

};

function getById(id) {
    return dispatch => {
        dispatch(request());

        authorize().then(() => ordersService.get(id))
            .then(
                order => dispatch(success(order)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: ordersConstants.GET_REQUEST } }
    function success(order) { return { type: ordersConstants.GET_SUCCESS, order } }
    function failure(error) { return { type: ordersConstants.GET_FAILURE, error } }
}

function getAll() {
    return dispatch => {
        dispatch(request());

        authorize().then(() => ordersService.get())
            .then(
                orders => dispatch(success(orders)),
                error => dispatch(failure(error.toString()))
            );
    };

    function request() { return { type: ordersConstants.GETALL_REQUEST } }
    function success(orders) { return { type: ordersConstants.GETALL_SUCCESS, orders } }
    function failure(error) { return { type: ordersConstants.GETALL_FAILURE, error } }
}