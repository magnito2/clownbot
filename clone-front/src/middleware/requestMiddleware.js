import config from '../config';
import { userConstants } from '../constants';

export default function requestMiddleware({ dispatch, getState }) {
    return function(next){
        return function(action) {
            if (action.type.includes("REQUEST") && action.type !== userConstants.LOGIN_REQUEST) {
                console.log("request captured", action.type);

                const { tokens } = getState().authentication;

                if(typeof tokens === "undefined"){ return next(action);}
                // 1 minutes from now
                const refreshThreshold = new Date(Date.now() + 60000);
                const expiresAt = new Date(tokens.expires_at + "Z");

                if (tokens.refresh_token && refreshThreshold.getTime() > expiresAt.getTime() ) {
                    const requestOptions = {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + tokens.refresh_token, 'Content-Type': 'application/json' },
                    };

                    fetch(`${config.apiUrl}/api/token/refresh`, requestOptions)
                        .then(response => {
                            console.log("our response is ", response);
                            return response.json();
                        }).then(json => {
                            dispatch({type: userConstants.AUTH_TOKEN_REFRESHED, token: json});
                            window.location.reload();
                        }).catch(error=>{
                            dispatch({type: userConstants.AUTH_TOKEN_REFRESH_FAILURE, error: error});
                        });

                }
            }

            return next(action);
        }
    }
}
