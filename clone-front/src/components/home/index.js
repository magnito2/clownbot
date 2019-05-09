import React, { Component } from 'react';
import { MainWrapper } from '../wrappers/main';
import { connect } from 'react-redux';
import { ordersActions, settingsActions, portfoliosActions } from '../../actions';
import {allDeepEqual} from "../../helpers/compare-equal-arrays";
import {PortfolioChart} from "../sub-components/portfolio.chart";

class IndexPage extends Component {

    constructor(props) {
        super(props);
        this.state = {
            exchange: "BINANCE",
            exchange_accounts: [],
            portfolio: {
                labels : [],
                portfolios : {
                    'BINANCE': [],
                    'BITTREX': []
                },
                loaded:false
            }

        }
    }
    componentDidMount(){
        this.props.dispatch(ordersActions.getAll());
        this.props.dispatch(settingsActions.get());
        this.props.dispatch(portfoliosActions.get())
    }

    componentWillReceiveProps(nextProps) {

        let needs_update = false;
        Object.keys(nextProps.portfolio.portfolios).map(exchange => {
            if(!allDeepEqual([this.state.portfolio.portfolios[exchange], nextProps.portfolio.portfolios[exchange]])){
                needs_update = true
            }
        });
        if(needs_update){
            this.setState({
                portfolio: {
                    ...this.state.portfolio,
                    labels: nextProps.portfolio.labels,
                    portfolios: nextProps.portfolio.portfolios,
                    loaded: true
                }
            })
        }
    }

    render(){
        const {orders} = this.props;

        return (
            <MainWrapper>
                <div class="row m-t-25">
                    <div class="col-sm-12 col-lg-9">
                        <div class="overview-wrap">
                            <h2 class="title-1">Portfolio</h2>
                        </div>
                        <div class="overview-item overview-item--c1">
                            <div class="overview__inner">
                                <div class="overview-box clearfix">
                                    <div class="icon">
                                        <i class="zmdi zmdi-account-o"></i>
                                    </div>
                                    <div class="text">
                                        <h2>My</h2>
                                        <span>chart</span>
                                    </div>
                                    <div class="text pull-right">
                                        <form class="form-header" action="">
                                            <div class="form-group">
                                                <div class="form-check-inline form-check">
                                                    <label for="inline-radio1" class="form-check-label ">
                                                        <input type="radio" id="inline-radio1" name="inline-radios" value="option1" class="form-check-input"/><h2><span>All</span></h2>
                                                    </label>
                                                    <label for="inline-radio2" class="form-check-label ">
                                                        <input type="radio" id="inline-radio2" name="inline-radios" value="option2" class="form-check-input"/><h2><span>Binance</span></h2>
                                                    </label>
                                                    <label for="inline-radio3" class="form-check-label ">
                                                        <input type="radio" id="inline-radio3" name="inline-radios" value="option3" class="form-check-input"/><h2><span>Bittrex</span></h2>
                                                    </label>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                                <div class="overview-chart">
                                    {
                                        this.state.portfolio.loaded && <PortfolioChart labels={this.state.portfolio.labels} portfolios={this.state.portfolio.portfolios}/>
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-9">
                        <div class="overview-wrap">
                            <h2 class="title-1">Buys</h2>
                        </div>
                        <div class="table-responsive table--no-card m-b-40">
                            <table class="table table-borderless table-striped table-earning">
                                <thead>
                                <tr>
                                    <th>Exchange</th>
                                    <th>symbol</th>
                                    <th>price</th>
                                    <th>amount</th>
                                </tr>
                                </thead>
                                <tbody>

                                {orders.map(order => {
                                    if (order.side === "BUY" || order.side === "LIMIT_BUY") {
                                        return (
                                            <tr>
                                                <td>{order.exchange}</td>
                                                <td>{order.symbol}</td>
                                                <td>{order.price}</td>
                                                <td>{order.quantity}</td>
                                            </tr>
                                        )
                                    }
                                })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-9">
                        <div class="overview-wrap">
                            <h2 class="title-1">Sells</h2>
                        </div>
                        <div class="table-responsive table--no-card m-b-40">
                            <table class="table table-borderless table-striped table-earning">
                                <thead>
                                <tr>
                                    <th>Exchange</th>
                                    <th>symbol</th>
                                    <th>price</th>
                                    <th>amount</th>
                                </tr>
                                </thead>
                                <tbody>

                                {orders.map(order => {
                                    if (order.side === "SELL" || order.side === "LIMIT_SELL") {
                                        return (
                                            <tr>
                                                <td>{order.exchange}</td>
                                                <td>{order.symbol}</td>
                                                <td>{order.price}</td>
                                                <td>{order.quantity}</td>
                                            </tr>
                                        )
                                    }
                                })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </MainWrapper>);
    }
}

function mapStateToProps(state) {
    const { list } = state.orders;
    const {settings} = state;
    const {portfolio} = state;
    return {
        orders : list,
        settings,
        portfolio
    };
}

const connectedIndexPage = connect(mapStateToProps)(IndexPage);
export { connectedIndexPage as IndexPage };