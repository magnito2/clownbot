import React, { Component } from 'react';
import { connect } from "react-redux";
import {MainWrapper} from "../wrappers/main";
import {settingsActions} from "../../actions";
import {SettingForm} from "./settings.form";

function SettingsPage(props) {

    return (<MainWrapper>
        <div className="row">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <h4>EXCHANGE SETTINGS</h4>
                    </div>
                    <div class="card-body">
                        <p class="text-muted m-b-15">Lets tune up the bot</p>
                        <div class="default-tab">
                            <nav>
                                <div class="nav nav-tabs" id="nav-tab" role="tablist">
                                    <a class="nav-item nav-link active" id="nav-binance-tab" data-toggle="tab" href="#nav-binance" role="tab" aria-controls="nav-binance"
                                       aria-selected="true">Binance</a>
                                    <a class="nav-item nav-link" id="nav-bittrex-tab" data-toggle="tab" href="#nav-bittrex" role="tab" aria-controls="nav-bittrex"
                                       aria-selected="false">Bittrex</a>
                                </div>
                            </nav>
                            <div class="tab-content pl-3 pt-2" id="nav-tabContent">
                                <div class="tab-pane fade show active" id="nav-binance" role="tabpanel" aria-labelledby="nav-binance-tab">
                                    <SettingForm exchange="BINANCE"/>
                                </div>
                                <div class="tab-pane fade" id="nav-bittrex" role="tabpanel" aria-labelledby="nav-bittrex-tab">
                                    <SettingForm exchange="BITTREX"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </MainWrapper>)
}

export {  SettingsPage  };
export { SignalsPage } from './settings.choose-signals';