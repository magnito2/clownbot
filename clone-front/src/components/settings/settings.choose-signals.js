import React, { Component } from 'react';
import { connect } from "react-redux";
import {signalsActions, settingsActions, alertActions} from "../../actions";
import {MainWrapper} from "../wrappers/main";
import {Spinner} from "../sub-components/spinner";
import {allDeepEqual} from "../../helpers/compare-equal-arrays";

class SignalsForm extends Component{
    constructor(props){
        super(props);
        this.state = {
            exchange : null,
            signals : [],
            checked_signals:[],
            submitted: false,
            exchange_accounts : [],
            account_signals_params : [], //store extra data on selected signals i.e percent investment and profit target,
            show_info: null
        };
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.showInfo = this.showInfo.bind(this);
        this.hideInfo = this.hideInfo.bind(this);
    }

    handleChange(e) {
        const { name} = e.target;
        if("signal" === name.split('-')[0]){
            const new_signals = this.state.checked_signals.slice();
            if (e.target.checked){
                new_signals.push(name.split('-')[1]);
                this.setState({
                    checked_signals : new_signals
                });
            }
            else{
                const index = new_signals.indexOf(name.split('-')[1]);
                new_signals.splice(index, 1);
                let new_acc_sig_params = this.state.account_signals_params.filter((acc_sig_param) => acc_sig_param.name !== name.split('-')[1]);
                this.setState({
                    checked_signals: new_signals,
                    account_signals_params: [...new_acc_sig_params]
                });
            }
        }
        else if(e.target.dataset.input_name === "profit_target" || e.target.dataset.input_name === "percent_investment"){
            const signal_name =  e.target.dataset.signal_name;
            const input_name =  e.target.dataset.input_name;
            const input_value =  e.target.value;
            if(input_name === 'profit_target'){
                if(isNaN(input_value)){
                    this.props.dispatch(alertActions.error('Invalid input, numbers only'));
                    return;
                }
                if(parseInt(input_value) < 1 || parseInt(input_value) > 20 ){
                    this.props.dispatch(alertActions.error('Profit target should be between 1% and 20%'));
                    return;
                }
            }
            if(input_name === 'percent_investment'){
                if(isNaN(input_value)){
                    this.props.dispatch(alertActions.error('Invalid input, numbers only'));
                    return;
                }
                if(parseInt(input_value) < 1 || parseInt(input_value) > 100 ){
                    this.props.dispatch(alertActions.error('Investment Percent should be between 1% and 100%'));
                    return;
                }
            }
            const params_arr = this.state.account_signals_params.filter((acc_sig_param) => acc_sig_param.name === signal_name );
            if (params_arr.length){
                let params = params_arr[0];
                params = {
                    ...params,
                    [input_name]: input_value
                };
                let new_acc_sig_params = this.state.account_signals_params.filter((acc_sig_param) => acc_sig_param.name !== signal_name);
                this.setState({
                    account_signals_params: [...new_acc_sig_params, params]
                });
            }
            else{
                let params = {
                    'name': signal_name,
                    [input_name]: input_value
                };
                this.setState({
                    account_signals_params: [...this.state.account_signals_params, params]
                });
            }
        }
        else{
            const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
            if(name === "exchange"){
                this.props.dispatch(signalsActions.getCheckedSignals(value));
            }
            this.setState({ [name]: value });
        }
    }

    componentDidMount(){
        this.props.dispatch(signalsActions.get(null));
        this.props.dispatch(settingsActions.get());
    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const { exchange, checked_signals, account_signals_params } = this.state;
        const { dispatch } = this.props;
        if (exchange) {
            dispatch(signalsActions.create({exchange_account: exchange, signals: checked_signals, account_signals_params}));
        }
    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.signals) {
            if(nextProps.signals.list.length > 0){
                this.setState({ signals: nextProps.signals.list });
            }
            if(!allDeepEqual([nextProps.signals.checked_signals, this.state.checked_signals])){
                this.setState({checked_signals: nextProps.signals.checked_signals})
            }
            if(!allDeepEqual([nextProps.signals.extra_params, this.state.account_signals_params])){
                this.setState({account_signals_params: nextProps.signals.extra_params})
            }
        }
        if (nextProps.settings){
            this.setState({exchange_accounts: nextProps.settings.accounts});
        }
    }

    showInfo(e){
        const input_name =  e.target.dataset.input_name;
        this.setState({show_info: input_name})
    }

    hideInfo(){
        this.setState({show_info: null});
    }

    render(){
        const { exchange, submitted, signals, exchange_accounts, checked_signals } = this.state;
        const { loading } = this.props.signals;

        return (<MainWrapper>
            <form class="" onSubmit={this.handleSubmit}>
                <div className="row">
                    <div className="col-md-9">
                        <div class="card">
                            <div class="card-header">
                                <strong>Signals</strong>
                            </div>
                            <div class="card-body card-block">
                                <div class="form-group">
                                    <label for="company" class=" form-control-label">Exchange</label>
                                    <select name="exchange" id="selectLg" class="form-control-lg form-control" onChange={this.handleChange}>
                                        <option value="">Choose Account</option>
                                        {
                                            exchange_accounts && exchange_accounts.map ( acc => <option value={acc.exchange_account_id}>{acc.exchange}</option>)
                                        }
                                    </select>
                                </div>
                                {
                                    exchange ?
                                        <div>
                                            <div class="form-group">
                                                <div class="form-check">
                                                    {
                                                        signals.map(signal => {
                                                            const sig_params_l = this.state.account_signals_params.filter(sig_p => sig_p.name === signal.name);
                                                            const sig_params = sig_params_l.length ? sig_params_l[0] : {};
                                                            return (
                                                                <div>
                                                                    <div class="checkbox">
                                                                        <label for="checkbox1" class="form-check-label ">
                                                                            <input type="checkbox" id={'checkbox-' + signal.name}
                                                                                   name={"signal-" + signal.name} checked={checked_signals.includes(signal.name)}
                                                                                   class="form-check-input" onChange={this.handleChange}/>{signal.name}
                                                                        </label>
                                                                    </div>
                                                                    {checked_signals.includes(signal.name) && <div class="row form-group">
                                                                        <div class="col col-md-7">
                                                                            <div className="input-group">
                                                                                <div className="input-group-addon">Investment Percent <span class="badge badge-secondary">Optional</span></div>
                                                                                <input
                                                                                    type="text"
                                                                                    name={signal.name+"-percent_investment"}
                                                                                    data-signal_name={signal.name}
                                                                                    data-input_name="percent_investment"
                                                                                    onChange={this.handleChange}
                                                                                    placeholder="Investment Percent"
                                                                                    value={sig_params.percent_investment ? sig_params.percent_investment : ''}
                                                                                    className="form-control"
                                                                                    onFocus={this.showInfo}
                                                                                    onBlur={this.hideInfo}
                                                                                />
                                                                            </div>
                                                                        </div>
                                                                        <div class="col col-md-5">
                                                                            <div className="input-group">
                                                                                <div className="input-group-addon">Profit Target <span class="badge badge-secondary">Optional</span></div>
                                                                                <input
                                                                                    type="text"
                                                                                    name={signal.name+"-profit_target"}
                                                                                    onChange={this.handleChange}
                                                                                    data-signal_name={signal.name}
                                                                                    data-input_name="profit_target"
                                                                                    placeholder="Profit Target Percent"
                                                                                    value={sig_params.profit_target ? sig_params.profit_target : ''}
                                                                                    className="form-control"
                                                                                    onFocus={this.showInfo}
                                                                                    onBlur={this.hideInfo}
                                                                                />
                                                                            </div>
                                                                        </div>
                                                                    </div>}
                                                                </div>
                                                            )
                                                        })
                                                    }
                                                </div>
                                            </div>
                                            <div class="form-actions form-group">
                                                <button type="submit" class="btn btn-success btn-sm">Submit <Spinner loading={loading}/></button>
                                            </div>
                                        </div>
                                        : ''
                                }
                            </div>
                        </div>
                    </div>
                    <div className="col-md-3">
                        <div className="card">
                            <div class="card-header">
                                <strong>Info</strong>
                            </div>
                            {this.state.show_info === "percent_investment" && <div className="card-body card-block">
                                <p className="card-text"><strong>Investment Percent</strong></p>
                                <p className="card-text">This field is <span class="badge badge-secondary">Optional</span></p>
                                <p class="card-text">
                                    Maximum amount of investment this signal can hold. Minimum value is 1% and max is 100%. For sources with
                                    high number of signals, use this to limit.
                                </p>
                            </div>}
                            {this.state.show_info === "profit_target" && <div className="card-body card-block">
                                <p className="card-text"><strong>Profit Target</strong></p>
                                <p className="card-text">This field is <span class="badge badge-secondary">Optional</span></p>
                                <p class="card-text">
                                    Control the profit target assigned to each signal. Sometimes, you trust one signal more than others. Assign
                                    a bigger profit target if a signal offers stronger signals
                                </p>
                            </div>}
                        </div>
                    </div>
                </div>
            </form>
        </MainWrapper>)
    }
}

function mapStateToProps(state) {
    const { signals, settings } = state;
    return {
        signals, settings
    };
}

const connectedSignalsForm = connect(mapStateToProps)(SignalsForm);
export { connectedSignalsForm as SignalsPage  };