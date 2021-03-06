import { combineReducers } from 'redux';

import { authentication } from './authentication.reducer';
import {orders} from "./orders.reducer";
import {settings} from "./settings.reducer";
import {signals} from "./signals.reducer";
import {portfolios} from "./portfolio.reducer";
import {manualorders} from "./manualorders.reducer";
import {trades} from "./trades.reducer";
import {assets} from "./assets.reducer";

import notifyReducer from 'react-redux-notify';

const rootReducer = combineReducers({
    authentication,
    orders,
    settings,
    signals,
    notifications: notifyReducer,
    portfolio: portfolios,
    manualorders,
    trades,
    assets
});

export default rootReducer;