import { portfoliosConstants } from "../constants";

const initialState = {
    portfolios : {},
    btc_values:[],
    labels:[]
};

export function portfolios(state = initialState, action) {

    switch (action.type)
    {
        case portfoliosConstants.GETALL_SUCCESS:
            console.log("our portfolios are", action.portfolios);
            return {
                ...state,
                portfolios: action.portfolio.portfolios,
                labels: action.portfolio.labels
            };
        case portfoliosConstants.GETALL_FAILURE:
            console.log("Failed to get portfolios");
            return {
                ...state,
                error: action.error
            };

        case portfoliosConstants.GET_SUCCESS:
            console.log("our portfolio is", action.portfolio);
            return {
                ...state,
                portfolios: action.portfolio.portfolios,
                labels: action.portfolio.labels
            };
        case portfoliosConstants.GET_FAILURE:
            console.log("Failed to get portfolio");
            return {
                ...state,
                error: action.error
            };

        case portfoliosConstants.GET_BTC_SUCCESS:
            console.log("btc values", action.portfolio);
            return {
                ...state,
                btc_values: action.portfolio
            };

        default:
            return state;
    }
}