import React, { Component } from 'react';
import { connect } from "react-redux";
import {settingsActions} from "../../actions";

class SettingsForm extends Component{
    constructor(props){
        super(props);
        this.state = {
            api_key : '',
            api_secret : '',
            exchange : this.props.exchange,
            profit_margin : '',
            stop_loss_trigger : '',
            order_cancel_seconds : '',
            min_order_size: '',
            submitted: false,
            account_exists: false,
            receive_notifications: '',
            user_tg_id: '',
            use_fixed_amount_per_order : '',
            fixed_amount_per_order : '',
            loading: false
        };
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        const { name } = e.target;
        const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
        this.setState({ [name]: value });
    }

    componentDidMount(){
        this.props.dispatch(settingsActions.get());
    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const {
            exchange, api_key, api_secret,
            profit_margin, stop_loss_trigger, order_cancel_seconds,
            min_order_size, account_exists, user_tg_id, receive_notifications,
            use_fixed_amount_per_order, fixed_amount_per_order
        } = this.state;
        const { dispatch } = this.props;
        if (exchange && api_key && api_secret && !account_exists) {
            dispatch(settingsActions.create({exchange, api_key, api_secret}));
        }
        else if(account_exists && profit_margin && stop_loss_trigger && order_cancel_seconds)
        {
            if(min_order_size || use_fixed_amount_per_order && fixed_amount_per_order){
                dispatch(settingsActions.create({
                    exchange, profit_margin, stop_loss_trigger, order_cancel_seconds, min_order_size, user_tg_id, receive_notifications,
                    use_fixed_amount_per_order, fixed_amount_per_order, api_secret, api_key
                }));
            }
        }
        this.setState({loading:true})

    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.settings.accounts.length > 0){
            const exchange_settings = nextProps.settings.accounts.find(acc => acc.exchange ===this.state.exchange);
            if (exchange_settings !== undefined){
                this.setState({account_exists: true});
            }
            else{
                return
            }
            if (exchange_settings.api_key !== this.state.api_key) {
                this.setState({ api_key: exchange_settings.api_key });
            }
            if (exchange_settings.api_secret !== this.state.api_secret) {
                this.setState({
                    api_secret: exchange_settings.api_secret,
                });
            }
            if (exchange_settings.profit_margin !== this.state.profit_margin) {
                this.setState({ profit_margin: exchange_settings.profit_margin });
            }
            if (exchange_settings.stop_loss_trigger !== this.state.stop_loss_trigger) {
                this.setState({ stop_loss_trigger: exchange_settings.stop_loss_trigger });
            }
            if (exchange_settings.order_cancel_seconds !== this.state.order_cancel_seconds) {
                this.setState({ order_cancel_seconds: exchange_settings.order_cancel_seconds });
            }
            if (exchange_settings.min_order_size !== this.state.min_order_size) {
                this.setState({ min_order_size: exchange_settings.min_order_size });
            }
            if (exchange_settings.user_tg_id !== this.state.user_tg_id) {
                this.setState({ user_tg_id: exchange_settings.user_tg_id });
            }
            if (exchange_settings.receive_notifications !== this.state.receive_notifications) {
                this.setState({ receive_notifications: exchange_settings.receive_notifications });
            }
            if (exchange_settings.use_fixed_amount_per_order !== this.state.use_fixed_amount_per_order) {
                this.setState({ use_fixed_amount_per_order: exchange_settings.use_fixed_amount_per_order });
            }
            if (exchange_settings.fixed_amount_per_order !== this.state.fixed_amount_per_order) {
                this.setState({ fixed_amount_per_order: exchange_settings.fixed_amount_per_order });
            }
        }
    }

    render(){
        const {
            api_key, api_secret, exchange, profit_margin, stop_loss_trigger,
            order_cancel_seconds, min_order_size, submitted, account_exists,
            user_tg_id, receive_notifications, use_fixed_amount_per_order, fixed_amount_per_order
        } = this.state;

        return (
            <form class="" onSubmit={this.handleSubmit}>
                <input type="hidden" name="exchange" value={exchange}/>
                <div class="form-group">
                    <label>Api Key</label>
                    <input type="text" className="au-input au-input--full" name="api_key" value={api_key} onChange={this.handleChange} />
                    {submitted && !account_exists && !api_key &&
                    <div className="help-block">Api Key is required</div>
                    }
                </div>
                <div class="form-group">
                    <label>Api Secret</label>
                    <input type="text" className="au-input au-input--full" name="api_secret" value={api_secret} default="*********" onChange={this.handleChange} />
                    {submitted && !account_exists && !api_secret &&
                    <div className="help-block">Api Secret is required</div>
                    }
                </div>
                {account_exists &&
                <div className="card">
                    <div className="card-body">
                        <div className="form-group">
                            <label>Profit Margin</label>
                            <div class="input-group">
                                <input type="text" name="profit_margin"  class="form-control" value={profit_margin} onChange={this.handleChange}/>
                                    <div class="input-group-addon">%</div>
                            </div>
                            {submitted && !profit_margin &&
                            <div className="help-block">Profit Margin is required</div>
                            }
                        </div>
                        <div class="form-group">
                            <label>Stop Loss Trigger</label>
                            <div class="input-group">
                                <div class="input-group-addon">
                                    <i class="fa fa-minus"></i>
                                </div>
                                <input type="text" name="stop_loss_trigger" value={stop_loss_trigger} onChange={this.handleChange} class="form-control"/>
                                <div class="input-group-addon">%</div>
                            </div>
                            {submitted && !stop_loss_trigger &&
                            <div className="help-block">Stop Loss is required</div>
                            }
                        </div>
                        <div class="form-group">
                            <label>Order Timeout</label>
                            <div class="input-group">
                                <div class="input-group-addon">
                                    <i class="fa fa-minus-circle"></i>
                                </div>
                                <input type="text" name="order_cancel_seconds" value={order_cancel_seconds} onChange={this.handleChange} class="form-control"/>
                                    <div class="input-group-addon">Sec</div>
                            </div>
                            {submitted && !order_cancel_seconds &&
                            <div className="help-block">Order Cancel Seconds is required</div>
                            }
                        </div>
                        { !use_fixed_amount_per_order &&
                        <div class="form-group">
                            <label>Min Order Size</label>
                            <div class="input-group">
                                <input type="text" name="min_order_size" value={min_order_size} onChange={this.handleChange} class="form-control"/>
                                <div class="input-group-addon">%</div>
                            </div>
                            {submitted && !min_order_size && !use_fixed_amount_per_order &&
                            <div className="help-block">Min Order Size is required or specify a fixed amount per order</div>
                            }
                        </div>
                        }
                        <div className="form-group">
                            <div className="form-check">
                                <div class="checkbox">
                                    <label for="checkbox333" class="form-check-label ">
                                        <input type="checkbox" id='checkbox333'
                                               name="use_fixed_amount_per_order" checked={use_fixed_amount_per_order}
                                               class="form-check-input" onChange={this.handleChange}/>Use fixed amount per order
                                    </label>
                                </div>
                            </div>
                            {use_fixed_amount_per_order &&
                            <div>
                                <label>Amount Per Order</label>
                                <div class="input-group">
                                    <input type="text" name="fixed_amount_per_order" value={fixed_amount_per_order} onChange={this.handleChange} class="form-control"/>
                                </div>
                                { submitted && !fixed_amount_per_order && use_fixed_amount_per_order &&
                                <div className="help-block">Enter the amount to use per order</div>
                                }
                            </div>
                            }
                        </div>
                        <div class="form-group">
                            <label>Telegram Account ID</label>
                            <div class="input-group">
                                <input type="text" name="user_tg_id" value={user_tg_id} onChange={this.handleChange} class="form-control"/>
                            </div>
                            {submitted && !user_tg_id &&
                            <div className="help-block">Enter your telegram  ID</div>
                            }
                        </div>
                        <div className="form-group">
                            <div className="form-check">
                                <div class="checkbox">
                                    <label for="checkbox332" class="form-check-label ">
                                        <input type="checkbox" id='checkbox332'
                                               name="receive_notifications" checked={receive_notifications}
                                               class="form-check-input" onChange={this.handleChange}/>Receive Notifications
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                }
                <div class="form-actions form-group">
                    <button type="submit" class="btn btn-success btn-sm">Submit</button>
                    {this.props.settings.loading && <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />}
                </div>


            </form>)
    }
}

function mapStateToProps(state) {
    const { settings } = state;
    return {
        settings
    };
}

const connectedSettingsForm = connect(mapStateToProps)(SettingsForm);
export { connectedSettingsForm as SettingForm  };