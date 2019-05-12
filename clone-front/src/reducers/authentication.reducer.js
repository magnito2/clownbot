import { userConstants } from '../constants';

let user = JSON.parse(localStorage.getItem('user'));
const initialState = user ? { loggedIn: true, user: user.user, tokens : user.tokens } : {};

export function authentication(state = initialState, action) {
    switch (action.type) {
        case userConstants.LOGIN_REQUEST:
            return {
                loggingIn: true,
                user: action.user
            };
        case userConstants.LOGIN_SUCCESS:
            return {
                loggedIn: true,
                user: action.user.user,
                tokens: action.user.tokens
            };
        case userConstants.LOGIN_FAILURE:
            return {};
        case userConstants.LOGOUT:
            return {};
        case userConstants.AUTH_TOKEN_REFRESHED:
            console.log("We are here", action.token.access_token);
            return {
                ...state,
                tokens : {
                    ...state.tokens,
                    access_token : action.token.access_token,
                    expires_at : action.token.expires_at
                }
            };
        case userConstants.AUTH_TOKEN_REFRESH_FAILURE:
            console.log("Failed to refresh token ", action.error);
            return {};
        case userConstants.REGISTER_REQUEST:
            return {
                ...state,
                loggingIn: true,
            }
        case userConstants.REGISTER_SUCCESS:
            return {
                user: action.user.user,
                tokens: action.user.tokens,
            };

        default:
            return state
    }
}