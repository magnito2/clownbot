import {createStore, applyMiddleware, compose} from "redux";
import rootReducer from "../reducers/index";
import requestMiddleware from "../middleware/requestMiddleware"
import thunk from "redux-thunk";

const storeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

const store = createStore(
    rootReducer,
    storeEnhancers(applyMiddleware(thunk, requestMiddleware))
);

export default store;