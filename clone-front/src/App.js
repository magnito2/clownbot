import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import 'react-redux-notify/dist/ReactReduxNotify.css';

import { Route, Router } from "react-router-dom";
import { history } from './helpers/history';
import {PrivateRoute} from "./components/PrivateRoute";

import {IndexPage} from "./components/home/index";
import {SettingsPage, SignalsPage} from "./components/settings";
import {LoginPage} from "./components/auth";
import {RegisterPage} from "./components/auth";
import {ManualOrderForm} from "./components/manualorders";

class App extends Component {
  render() {
    return (
        <Router history={history}>
          <div class="outer-wrapper">
            <PrivateRoute path="/" exact component={IndexPage} />
            <PrivateRoute path="/settings" component={SettingsPage} />
              <PrivateRoute path="/signals" component={SignalsPage} />
              <PrivateRoute path="/manualorders" component={ManualOrderForm} />
            <Route path="/login" component={LoginPage} />
            <Route path="/register" component={RegisterPage} />
          </div>
        </Router>
    );
  }
}

export default App;
