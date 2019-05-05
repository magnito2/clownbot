import config from '../config';
import { authHeader } from '../helpers';

export const settingsService = {
    create,
    update,
    get,
    createAvatar,
};

function create(settings) {
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify( settings )
    };

    return fetch(`${config.apiUrl}/api/exchange/settings`, requestOptions)
        .then(handleResponse)
        .then(settings => {
            return settings;
        });
}

function createAvatar(avatar) {
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify(avatar)
    };

    return fetch(`${config.apiUrl}/api/settings/avatar`, requestOptions)
        .then(handleResponse)
        .then(settings => {
            return settings;
        });
}

function get() {
    const requestOptions = {
        method: 'GET',
        headers: authHeader()
    };

    return fetch(`${config.apiUrl}/api/exchange/settings`, requestOptions).then(handleResponse);
}

function update(settings) {
    const requestOptions = {
        method: 'PUT',
        headers: { ...authHeader(), 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    };

    return fetch(`${config.apiUrl}/api/exchange/settings`, requestOptions).then(handleResponse);
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