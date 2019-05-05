import React, { Component } from 'react';
import { connect } from "react-redux";
import {signalsActions, settingsActions} from "../../actions";
import {MainWrapper} from "../wrappers/main";

class SignalsForm extends Component{
    constructor(props){
        super(props);
        this.state = {
            exchange : null,
            signals : [],
            checked_signals : [],
            submitted: false,
            exchange_accounts : []
        };
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        const { name} = e.target;
        if("signal" === name.split('-')[0]){
            const new_signals = this.state.checked_signals.slice();
            if (e.target.checked){
                new_signals.push(name.split('-')[1]);
            }
            else{
                const index = new_signals.indexOf(name.split('-')[1]);
                new_signals.splice(index, 1);
            }
            this.setState({
                checked_signals : new_signals
            })
        }else{
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
        const { exchange, checked_signals } = this.state;
        const { dispatch } = this.props;
        if (exchange) {
            dispatch(signalsActions.create({exchange_account: exchange, signals: checked_signals}));
        }
    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.signals) {
            if(nextProps.signals.list.length > 0){
                this.setState({ signals: nextProps.signals.list });
            }
            if(nextProps.signals.checked_signals.length > 0){
                this.setState({checked_signals: nextProps.signals.checked_signals});
            }
        }
        if (nextProps.settings){
            this.setState({exchange_accounts: nextProps.settings.accounts});
        }
    }

    render(){
        const { exchange, submitted, signals, exchange_accounts, checked_signals } = this.state;

        return (<MainWrapper>
            <form class="" onSubmit={this.handleSubmit}>
                <div className="col-lg-10">
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
                                                        return (
                                                            <div class="checkbox">
                                                                <label for="checkbox1" class="form-check-label ">
                                                                    <input type="checkbox" id={'checkbox-' + signal.name}
                                                                           name={"signal-" + signal.name} checked={checked_signals.includes(signal.name)}
                                                                           class="form-check-input" onChange={this.handleChange}/>{signal.name}
                                                                </label>
                                                            </div>
                                                        )
                                                    })
                                                }
                                            </div>
                                        </div>
                                        <div class="form-actions form-group">
                                            <button type="submit" class="btn btn-success btn-sm">Submit</button>
                                        </div>
                                    </div>
                                    : ''
                            }
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