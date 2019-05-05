import store from '../store/index';

export function authHeader() {
    // return authorization header with jwt token
    let user = JSON.parse(localStorage.getItem('user'));
    const { tokens } = store.getState().authentication;

    if (tokens && tokens.access_token){
        return { 'Authorization': 'Bearer ' + tokens.access_token };
    }
    else if (user && user.tokens.access_token) {
        return { 'Authorization': 'Bearer ' + user.tokens.access_token };
    } else {
        return {};
    }
}