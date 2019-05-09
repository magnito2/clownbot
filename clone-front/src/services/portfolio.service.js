import config from '../config';
import { authHeader } from '../helpers';
import querystring from 'querystring';

export const portfoliosService = {
    get,
    getBTCValues
};

function get() {
    const requestOptions = {
        method: 'GET',
        headers: authHeader()
    };
    return fetch(`${config.apiUrl}/api/portfolios`, requestOptions).then(handleResponse);
}

function getBTCValues() {
    const requestOptions = {
        method: 'GET',
        headers: authHeader()
    };
    return fetch(`${config.apiUrl}/api/portfolios/btc-values`, requestOptions).then(handleResponse);
}

function handleResponse(response) {
    return response.text().then(text => {
        const data = text && JSON.parse(text);
        if (!response.ok) {
            if (response.status === 401) {

            }

            const error = (data && data.message) || response.statusText;
            return Promise.reject(error);
        }

        return data;
    });
}