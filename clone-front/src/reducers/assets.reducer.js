import { assetsConstants } from "../constants";

const initialState = {
    list : [],
    accounts : []
};

export function assets(state = initialState, action) {

    switch (action.type)
    {
        case assetsConstants.GETALL_SUCCESS:
            return {
                ...state,
                list: action.assets.assets,
                accounts: action.assets.accounts
            };
        case assetsConstants.GETALL_FAILURE:
            console.log("Failed to get assets");
            return {
                ...state,
                error: action.error
            };

        case assetsConstants.GET_SUCCESS:
            return {
                ...state,
                list: [...state.assets.list, action.asset.assets]
            };
        case assetsConstants.GET_FAILURE:
            console.log("Failed to get asset");
            return {
                ...state,
                error: action.error
            };

        default:
            return state;
    }
}