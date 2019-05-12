import {settingsConstants} from "../constants";

const initialState = {
    accounts: [],
    loading: false
};

export function settings(state = initialState, action) {

    switch (action.type)
    {
        case settingsConstants.CREATE_REQUEST:
            return {
                ...state,
                loading : true
            };
        case settingsConstants.CREATE_SUCCESS:
        case settingsConstants.CREATE_FAILURE:
            return {
                ...state,
                loading : false
            };

        case settingsConstants.GET_REQUEST:
            return {
                ...state,
                loading : true
            };
        case settingsConstants.GET_SUCCESS:
            return {
                ...state,
                accounts : [...action.settings],
                loading: false
            };
        case settingsConstants.GET_FAILURE:
            return {
                ...state,
                error: action.error
            };
        case  settingsConstants.UPDATE_SUCCESS:
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