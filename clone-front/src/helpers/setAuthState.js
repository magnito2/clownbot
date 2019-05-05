import store from '../store/index';

export function setAuthState(state) {
    try {
        localStorage.setItem('state.auth.tokens', JSON.stringify((state.authentication || {}).tokens));
        const user_string = localStorage.getItem('user');
        const user = JSON.parse(user_string);
        let new_user = {
            ...user,
            tokens : {
                ...user.tokens,
                access_token : state.authentication.tokens.access_token,
                expires_at : state.authentication.tokens.expires_at
            }
        }
        localStorage.setItem("user", JSON.stringify(new_user));

    } catch (err) { return undefined; }
}

store.subscribe(() => {
    setAuthState(store.getState())
});