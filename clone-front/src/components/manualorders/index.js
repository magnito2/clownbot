import React, { Component } from 'react';
import { connect } from "react-redux";
import {MainWrapper} from "../wrappers/main";
import {manualordersActions, settingsActions} from "../../actions";
import {ReactSelectize, SimpleSelect, MultiSelect} from 'react-selectize';

class ManualOrdersForm extends Component{

    constructor(props){
        super(props);
        this.state = {
            exchange_account_id:'',
            symbol:'',
            side:'',
            price:'',
            quantity:'',
            exchange_accounts : '',
            submitted:false,
            exchange_symbols : {
                exchange : '',
                symbols : [],
                loading: true
            },
            exchange: null

        }
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(e) {
        const { name } = e.target;
        const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
        this.setState({ [name]: value });
        if(name === "exchange_account_id"){
            const exchange_list = this.state.exchange_accounts.filter(exchange => exchange.exchange_account_id === parseInt(value));
            if (exchange_list.length > 0){
                const exchange = exchange_list[0];
                this.props.dispatch(manualordersActions.getSymbols(exchange.exchange));
                this.setState({exchange_symbols :{
                    ...this.state.exchange_symbols,
                    loading: true
                }});
                this.setState({
                    exchange: exchange.exchange,
                })
            }
        }
    }

    componentDidMount(){
        this.props.dispatch(settingsActions.get());
    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.settings){
            this.setState({exchange_accounts: nextProps.settings.accounts});
        }
        if (nextProps.manualorders){
            const {symbols} = nextProps.manualorders;
            if(symbols.symbols.length > 0){
                this.setState({exchange_symbols: {
                    exchange: symbols.exchange,
                    symbols: symbols.symbols,
                    loading: false
                }})
            }
        }


    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const {exchange_account_id, symbol, side, price, quantity, exchange} = this.state;
        if (exchange_account_id && symbol && side && price && quantity && exchange ){
            this.props.dispatch(manualordersActions.create({exchange_account_id, symbol, side, price, quantity, exchange}));
        }

    }

    render(){

        const {exchange_account_id, exchange_accounts, exchange_symbols, symbol, side, price, quantity, submitted} = this.state;
        const btc_re = /^([A-Z]{3}|[A-Z]{4})BTC/
        return (<MainWrapper>
            <form class="" onSubmit={this.handleSubmit}>
                <div className="col-lg-10">
                    <div class="card">
                        <div class="card-header">
                            <strong>Create Order</strong>
                        </div>
                        <div class="card-body card-block">
                            <div class="form-group">
                                <label for="company" class=" form-control-label">Exchange</label>
                                <select name="exchange_account_id" id="select_id" class="form-control-lg form-control" onChange={this.handleChange}>
                                    <option value="">Choose Exchange Account</option>
                                    {
                                        exchange_accounts && exchange_accounts.map ( acc => <option value={acc.exchange_account_id}>{acc.exchange}</option>)
                                    }
                                </select>
                                {
                                    exchange_account_id && <div>
                                        <div class="form-group">
                                            <label for="company" class=" form-control-label">Symbol</label>
                                            {
                                                    exchange_symbols.loading ? <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />

                                                : <select name="symbol" id="select_id_2" class="form-control-lg form-control" onChange={this.handleChange}>
                                                <option value="">choose a symbol</option>
                                                {
                                                    !exchange_symbols.loading && exchange_symbols.symbols.map ( symbol => <option value={symbol}>{symbol}</option>)
                                                }
                                            </select>}
                                            {submitted && !symbol &&
                                            <div className="help-block">You have to select a symbol</div>
                                            }
                                        </div>
                                        {symbol &&
                                        <div class="form-group">
                                            <label>PRICE</label>
                                            <div class="input-group">
                                                <div class="input-group-addon">
                                                    <i class="fa fa-minus"></i>
                                                </div>
                                                <input type="text" name="price" value={price} onChange={this.handleChange} class="form-control"/>
                                                <div class="input-group-addon">%</div>
                                            </div>
                                            {submitted && !price &&
                                            <div className="help-block">What price</div>
                                            }
                                        </div>
                                        }
                                        {price &&
                                        <div class="form-group">
                                            <label>QUANTITY</label>
                                            <div class="input-group">
                                                <div class="input-group-addon">
                                                    <i class="fa fa-minus"></i>
                                                </div>
                                                <input type="text" name="quantity" value={quantity}
                                                       onChange={this.handleChange} class="form-control"/>
                                                <div class="input-group-addon">%</div>
                                            </div>
                                            {submitted && !quantity &&
                                            <div className="help-block">How much {btc_re.exec(symbol) ? btc_re.exec(symbol)[1] : '*specify symbol'}</div>
                                            }
                                        </div>
                                        }
                                        {quantity &&
                                        <div class="form-group">
                                            <label>SIDE</label>
                                            <select name="side" id="select_side" class="form-control-lg form-control" onChange={this.handleChange}>
                                                <option value="">Buy or Sell</option>
                                                <option value="BUY">BUY</option>
                                                <option value="SELL">SELL</option>
                                            </select>
                                            {submitted && !side &&
                                            <div className="help-block">Do we buy it or sell it</div>
                                            }
                                        </div>
                                        }
                                    </div>
                                }
                                {side &&
                                    <div class="form-actions form-group">
                                        <button type="submit" class="btn btn-primary btn-lg pull-right">PLACE ORDER</button>
                                    </div>}
                            </div>

                        </div>
                    </div>
                </div>
            </form>
        </MainWrapper>)
    }
}

function mapStateToProps(state) {
    const { settings, manualorders } = state;
    return {
        settings, manualorders
    };
}

const connectedOrderForm = connect(mapStateToProps)(ManualOrdersForm);
export { connectedOrderForm as ManualOrderForm  };