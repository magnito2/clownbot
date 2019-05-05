import {signalsConstants} from "../constants";

const initialState = {

};

export function signals(state = initialState, action) {

    switch (action.type)
    {
        case signalsConstants.GET_SUCCESS:
            console.log("our signals are", action.signals);
            return action.signals;
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
        default:
            return state;
    }
}