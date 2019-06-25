import { tradesConstants } from "../constants";

const initialState = {
    list : []
};

export function trades(state = initialState, action) {

    switch (action.type)
    {
        case tradesConstants.GETALL_SUCCESS:
            return {
                ...state,
                list: action.trades
            };
        case tradesConstants.GETALL_FAILURE:
            console.log("Failed to get trades");
            return {
                ...state,
                error: action.error
            };

        case tradesConstants.GET_SUCCESS:
            return {
                ...state,
                list: [...state.trades.list, action.trade]
            };
        case tradesConstants.GET_FAILURE:
            console.log("Failed to get trade");
            return {
                ...state,
                error: action.error
            };

        default:
            return state;
    }
}