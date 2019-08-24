import React, { Component } from 'react';
import { connect } from "react-redux";
import {MainWrapper} from "../wrappers/main";
import {assetsActions, alertActions} from "../../actions";

class AssetsPage extends Component{
    constructor(props){
        super(props);
        this.state = {
            exchange_accounts : '',
            assets: [],
            exchange: null,
            loading: false,
        }
        this.handleChange = this.handleChange.bind(this);
    }

    componentDidMount(){
        this.props.dispatch(assetsActions.getAll());
    }

    handleChange(e) {
        const { name } = e.target;
        const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
        this.setState({ [name]: value });
        if(name === "exchange_account_id"){
            const exchange_list = this.state.exchange_accounts.filter(exchange => exchange.exchange_account_id === parseInt(value));
            if (exchange_list.length > 0){
                const exchange = exchange_list[0];
                this.setState({
                    exchange: exchange.exchange,
                });
            }
        }
    }

    componentWillReceiveProps(nextProps) {
        if (nextProps.assets){
            if (nextProps.assets.accounts){
                this.setState({exchange_accounts: nextProps.assets.accounts});
            }
            if (nextProps.assets.list){
                this.setState({assets: nextProps.assets.list});
            }
        }
    }
    render(){
        const {exchange_accounts} = this.state;
        const assets = this.state.assets[this.state.exchange];
        return (
            <MainWrapper>
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
                            </div>
                            <div class="table-responsive m-b-40">
                                <table class="table table-borderless table-data3">
                                    <thead>
                                    <tr>
                                        <th>name</th>
                                        <th>exchange</th>
                                        <th>free</th>
                                        <th>locked</th>
                                        <th>BTC value</th>
                                    </tr>
                                    </thead>
                                    <tbody>
                                    {assets && assets.map(asset =>
                                        <tr>
                                            <td>{asset.name}</td>
                                            <td>{asset.exchange}</td>
                                            <td>{asset.free}</td>
                                            <td>{asset.locked}</td>
                                            <td>---</td>
                                        </tr>
                                    )}

                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </MainWrapper>
        );
    }
}

function mapStateToProps(state) {
    const { assets } = state;
    return {
        assets
    };
}

const connectedAssetsPage = connect(mapStateToProps)(AssetsPage);
export { connectedAssetsPage as AssetsPage  };