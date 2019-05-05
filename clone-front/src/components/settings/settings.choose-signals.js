import React, { Component } from 'react';
import { connect } from "react-redux";
import {signalsActions} from "../../actions";
import {MainWrapper} from "../wrappers/main";

class SignalsForm extends Component{
    constructor(props){
        super(props);
        this.state = {
            exchange : null,
            signals : [],
            checked_signals : [],
            submitted: false
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
            this.setState({ [name]: value });
        }
    }

    componentDidMount(){
        this.props.dispatch(signalsActions.get(null));
    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const { exchange, checked_signals } = this.state;
        const { dispatch } = this.props;
        if (exchange) {
            dispatch(signalsActions.create({exchange, signals: checked_signals}));
        }

    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.signals !== this.state.signals) {
            this.setState({ signals: nextProps.signals });
        }

    }

    render(){
        const { exchange, submitted, signals } = this.state;

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
                                    <option value="">Choose Exchange</option>
                                    <option value="binance">Binance</option>
                                    <option value="bittrex">Bittrex</option>
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
                                                                           name={"signal-" + signal.name} checked={signal.subscribed}
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
    const { signals } = state;
    return {
        signals
    };
}

const connectedSignalsForm = connect(mapStateToProps)(SignalsForm);
export { connectedSignalsForm as SignalsPage  };