import config from '../config';
import { authHeader } from '../helpers';
import querystring from 'querystring';

export const signalsService = {
    create,
    get,
    getCheckedSignals
};

function create(signals) {
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify( signals )
    };

    return fetch(`${config.apiUrl}/api/signals`, requestOptions)
        .then(handleResponse)
        .then(signals => {
            return signals;
        });
}

function get(exchange_account = null) {
    const requestOptions = {
        method: 'GET',
        headers: authHeader()
    };
    const params = {exchange_account };
    return fetch(`${config.apiUrl}/api/signals?${querystring.stringify(params)}`, requestOptions).then(handleResponse);
}

function getCheckedSignals(exchange_account) {
    const requestOptions = {
        method: 'GET',
        headers: authHeader()
    };
    const params = {exchange_account };
    return fetch(`${config.apiUrl}/api/checked-signals?${querystring.stringify(params)}`, requestOptions).then(handleResponse);
}

function handleResponse(response) {
    return response.text().then(text => {
        const data = text && JSON.parse(text);
        if (!response.ok) {
            if (response.status === 401) {
                // auto logout if 401 response returned from api
                //window.location.reload(true);
            }
            const error = (data && data.message) || response.statusText;
            return Promise.reject(error);
        }
        return data;
    });
}