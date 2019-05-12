import React, {Component} from 'react';
import { connect } from "react-redux";
import { Notify } from 'react-redux-notify';
import {DropdownLink} from "../sub-components/dropdown-link";
import {AccountMenu, Portfolio} from "../sub-components";
import {portfoliosActions} from "../../actions";
import {MobileNavigation} from "../mobile-nav/index";

class MainWrapper extends Component{

    constructor(props){
        super(props);
        this.state = {
            btc_values: []
        }
    }

    componentDidMount(){
        const {portfolio} = this.props;
        if(portfolio.btc_values.length === 0){
            this.props.dispatch(portfoliosActions.getBTCValues())
        }
        else{
            this.setState({btc_values: portfolio.btc_values})
        }
    }

    componentWillReceiveProps(nextProps) {
        if (nextProps.portfolio.btc_values.length) {
            this.setState({btc_values: nextProps.portfolio.btc_values})
        }
    }

    render () {
        const {user} = this.props;
        const {btc_values} = this.state;

        return (<body>
        <div class="page-wrapper">
            <MobileNavigation/>
            <aside class="menu-sidebar d-none d-lg-block">
                <div class="logo">
                    <a href="#">
                        <img src="images/icon/clown.png" alt="Clown" />
                    </a>
                </div>
                <div class="menu-sidebar__content js-scrollbar1">
                    <nav class="navbar-sidebar">
                        <ul class="list-unstyled navbar__list">
                            <li>
                                <a href="/"><i class="fas fa-tachometer-alt"></i>Dashboard</a>
                            </li>
                            <li>
                                <a href="/settings">
                                    <i class="fas fa-chart-bar"></i>Settings</a>
                            </li>
                            <li>
                                <a href="/signals">
                                    <i class="fas fa-chart-line"></i>Signals</a>
                            </li>
                            <li>
                                <a href="/manualorders">
                                    <i class="fas fa-bank"></i>Create Order</a>
                            </li>
                        </ul>
                    </nav>
                </div>
            </aside>
            <div class="page-container">
                <header class="header-desktop">
                    <div class="section__content section__content--p30">
                        <div class="container-fluid">
                            <div class="header-wrap">
                                <div></div>
                                <div class="header-button">
                                    <Portfolio btc_values={btc_values}/>
                                    <AccountMenu user={user}/>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>
                <div class="main-content">
                    <div class="section__content section__content--p30">
                        <div class="container-fluid">
                            <Notify/>
                            {alert.message &&
                            <div className={`alert ${alert.type}`}>{alert.message}</div>
                            }
                            {this.props.children}
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="copyright">
                                        <p>Copyright © 2019 Magnito.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </body>);
    }
}

function mapStateToProps(state) {
    const { user } = state.authentication;
    const { portfolio } = state;
    return {
        user, portfolio
    };
}

const Wrapper = connect(mapStateToProps)(MainWrapper);
export { Wrapper as MainWrapper  };
