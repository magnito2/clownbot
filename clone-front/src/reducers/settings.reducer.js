import {settingsConstants} from "../constants";

const initialState = {
    accounts: []
};

export function settings(state = initialState, action) {

    switch (action.type)
    {
        case settingsConstants.GET_SUCCESS:
            console.log("our settings are", action.settings);
            return {
                ...state,
                accounts : [...action.settings]
            };
        case settingsConstants.GET_FAILURE:
            console.log("Failed to get settings");
            return {
                ...state,
                error: action.error
            };
        case  settingsConstants.UPDATE_SUCCESS:
            console.log("success updating settings");
            return {
                ...state,
                accounts: state.accounts.concat(action.settings)
            }
        case settingsConstants.CREATE_AVATAR_REQUEST:
            return {
                ...state,
                avatar_creating: true
            }
        case settingsConstants.CREATE_AVATAR_SUCCESS:
            return {
                ...state,
                avatar_creating: false
            }
        default:
            return state;
    }
}