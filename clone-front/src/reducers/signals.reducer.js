import {signalsConstants} from "../constants";

const initialState = {
    list : [],
    checked_signals : [],
    loading: false,
};

export function signals(state = initialState, action) {

    switch (action.type)
    {
        case signalsConstants.GET_SUCCESS:
            console.log("our signals are", action.signals);
            return {
                ...state,
                list: action.signals,
                loading: false
            };
        case signalsConstants.GET_FAILURE:
            console.log("Failed to get signals");
            return {
                ...state,
                error: action.error,
                loading: false
            };
        case  signalsConstants.UPDATE_SUCCESS:
            console.log("success updating signals");
            return {
                ...state,
                ...action.signals,
                loading: false
            };
        case signalsConstants.GET_CHECKED_SUCCESS:
        case signalsConstants.CREATE_SUCCESS:
            console.log('recieved checked signals');
            return {
                ...state,
                checked_signals : action.signals,
                loading: false
            };
        case signalsConstants.GET_REQUEST:
        case signalsConstants.CREATE_REQUEST:
        case signalsConstants.GET_CHECKED_REQUEST:
            return{
                ...state,
                loading: true
            };
        case signalsConstants.CREATE_SUCCESS:
        case signalsConstants.CREATE_FAILURE:
            return {
                ...state,
                loading: false
            }

        default:
            return state;
    }
}