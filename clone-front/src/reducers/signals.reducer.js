import {signalsConstants} from "../constants";

const initialState = {
    list : [],
    checked_signals : []
};

export function signals(state = initialState, action) {

    switch (action.type)
    {
        case signalsConstants.GET_SUCCESS:
            console.log("our signals are", action.signals);
            return {
                ...state,
                list: action.signals,
            };
        case signalsConstants.GET_FAILURE:
            console.log("Failed to get signals");
            return {
                ...state,
                error: action.error
            };
        case  signalsConstants.UPDATE_SUCCESS:
            console.log("success updating signals");
            return {
                ...state,
                ...action.signals
            };
        case signalsConstants.GET_CHECKED_SUCCESS:
            console.log('recieved checked signals');
            return {
                ...state,
                checked_signals : action.signals,
            };

        default:
            return state;
    }
}