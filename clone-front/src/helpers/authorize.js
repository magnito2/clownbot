import store from '../store/index';
import config from '../config';
import { userConstants } from '../constants';

export const authorize = ()=> new Promise((resolve, reject) => {
    const { tokens } = store.getState().authentication;

    const refreshThreshold = new Date(Date.now() + 60000);
    const expiresAt = new Date(tokens.expires_at + "Z");
    if (tokens.refresh_token && refreshThreshold.getTime() > expiresAt.getTime()) {
        const requestOptions = {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + tokens.refresh_token, 'Content-Type': 'application/json' },
        };

        fetch(`${config.apiUrl}/api/token/refresh`, requestOptions)
            .then(response => {
                console.log("our response is ", response);
                return response.json();
            }).then(json => {
            store.dispatch({type: userConstants.AUTH_TOKEN_REFRESHED, token: json});
            resolve({token : json});
        }).catch(error=>{
            store.dispatch({type: userConstants.AUTH_TOKEN_REFRESH_FAILURE, error: error});
            reject(error);
        });
    }
    resolve();
});