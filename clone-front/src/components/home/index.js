import React, { Component } from 'react';
import { MainWrapper } from '../wrappers/main';
import { connect } from 'react-redux';
import { ordersActions, settingsActions, portfoliosActions, tradesActions } from '../../actions';
import {allDeepEqual} from "../../helpers/compare-equal-arrays";
import {PortfolioChart} from "../sub-components/portfolio.chart";
import {IndexOrdersTable} from "../sub-components/index-orders-table";

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
            },
            activePage: 1,

        }
    }
    componentDidMount(){
        this.props.dispatch(ordersActions.getAll());
        this.props.dispatch(settingsActions.get());
        this.props.dispatch(portfoliosActions.get());
        this.props.dispatch(tradesActions.getAll());
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
                    <div class="col-sm-12 col-lg-">
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
                <IndexOrdersTable orders = {orders} itemsCountPerPage={10}/>
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