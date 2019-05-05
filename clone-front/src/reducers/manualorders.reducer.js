import {manualordersConstants} from "../constants";

const initialState = {
    orders: [],
    symbols: {
        exchange : '',
        symbols : []
    }
};

export function manualorders(state = initialState, action) {

    switch (action.type)
    {
        case manualordersConstants.GET_SUCCESS:
            console.log("our manualorders are", action.manualorders);
            return {
                ...state,
                orders: action.manualorders
            };
        case manualordersConstants.GET_FAILURE:
            console.log("Failed to get manualorders");
            return {
                ...state,
                error: action.error
            };
        case  manualordersConstants.UPDATE_SUCCESS:
            console.log("success updating manualorders");
            return {
                ...state,
                orders: state.orders.concat(action.manualorders)
            };
        case manualordersConstants.GET_SYMBOLS_SUCCESS:
            console.log("our symbols are", action.symbols);
            return{
                ...state,
                symbols: action.symbols
            };
        default:
            return state;
    }
}