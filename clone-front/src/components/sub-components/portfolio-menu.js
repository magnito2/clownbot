import React, {Component} from 'react';

class Portfolio extends Component{

    constructor(props){
        super(props);
        this.state = {
            show_dropdown: false
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e){
        e.preventDefault();
        if (!this.state.show_dropdown){
            document.body.addEventListener('click', this.handleChange);
        }
        else{
            document.body.removeEventListener('click', this.handleChange);
        }
        this.setState({ show_dropdown: !this.state.show_dropdown });
    }


    render(){
        const {btc_values} = this.props;
        return (<div class="noti-wrap">
            <div className={this.state.show_dropdown ? "noti__item js-item-menu show-dropdown" : "noti__item js-item-menu"} onClick={this.handleChange}>
                <i class="zmdi zmdi-money-box"></i>
                <div class="notifi-dropdown js-dropdown">
                    <div class="notifi__title">
                        <p>Portfolio Balances</p>
                    </div>
                    {
                        btc_values && btc_values.map(btc_value =>
                            <div class="notifi__item">
                                <div class="content">
                                    <p>{btc_value.exchange} - {btc_value.btc_value} BTC</p>
                                    <span class="date">{btc_value.timestamp}</span>
                                </div>
                            </div>
                        )
                    }
                </div>
            </div>
        </div>);
    }
}

export {Portfolio}