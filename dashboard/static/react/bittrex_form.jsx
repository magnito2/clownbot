
class BittrexForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
        order_type:'',
        symbol:'',
        side: '',
        price: '',
        quantity: '',
        condition: false,
        condition_type: '',
        target: '',
        time_in_effect: 'GOOD_TIL_CANCELLED',
        alert: null
    };
    this.handleResponse = this.handleResponse.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

    handleChange = name => event => {
        this.setState({ [name]: event.target.type === "checkbox" ? event.target.checked : event.target.value });
    }

    handleSubmit(e) {
        e.preventDefault();

        this.setState({ submitted: true });
        const { order_type, symbol, side, price, quantity, condition_type, target } = this.state;

        const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_type, symbol, side, price, quantity, condition_type, target
            })
        };

        return fetch(`/api/bittrex/settings`, requestOptions)
            .then(this.handleResponse).then(data => {
                this.setState({alert: {
                    type: 'success',
                    message: data
                }})
            }).catch(error => {
                this.setState({alert: {
                    type: 'danger',
                    message: error
                }})
                }
            );

    }

    handleResponse(response) {
        return response.text().then(text => {
            const data = text && JSON.parse(text);
            if (!response.ok) {
                if (response.status === 401) {
                    // auto logout if 401 response returned from api
                    //window.location.reload(true);
                }

                const error = (data && data.message) || response.statusText;
                return Promise.reject(error);
            }
            return data;
        });
    }

  render() {

      return (
          <div className="container">
              {this.state.alert &&
              <div className={`alert alert-${this.state.alert.type}`} role="alert">{this.state.alert.message}</div> }
              <form onSubmit={this.handleSubmit}>
                  <div className="form-group">
                      <label htmlFor="symbol">Symbol</label>
                      <select className="form-control" id="symbol" name="symbol" value={this.state.symbol} onChange={this.handleChange('symbol')}>
                          <option>CHOOSE SYMBOL</option>
                          <option value="BTC-LTC">BTC-LTC</option>
                          <option value="USDT-OMG">USDT-OMG</option>
                          <option value="BTC-GO">BTC-GO</option>
                          <option value="USDT-BTC">USDT-BTC</option>
                          <option value="USDT-ETH">USDT-ETH</option>
                      </select>
                  </div>
                  <div className="form-group">
                      <label htmlFor="side">SIDE</label>
                      <select className="form-control" id="side" name="side" value={this.state.side} onChange={this.handleChange('side')}>
                          <option>CHOOSE SIDE</option>
                          <option value="buy">BUY</option>
                          <option value="sell">SELL</option>
                      </select>
                  </div>
                  <div className="form-group">
                      <label htmlFor="price">PRICE</label>
                      <input className="form-control" id="price" name="price" value={this.state.price} onChange={this.handleChange('price')}/>
                  </div>
                  <div className="form-group">
                      <label htmlFor="quantity">QUANTITY</label>
                      <input className="form-control" id="quantity" name="quantity" value={this.state.quantity} onChange={this.handleChange('quantity')}/>
                  </div>
                  <div className="form-group">
                      <label htmlFor="order-type">Order Type</label>
                      <select className="form-control" id="order-type" name="order_type" value={this.state.order_type} onChange={this.handleChange('order_type')}>
                          <option value="limit">LIMIT</option>
                          <option value="market">MARKET</option>
                      </select>
                  </div>
                  <div className="form-group form-check">
                      <input type="checkbox" className="form-check-input" id="stop_loss" value={this.state.stop_loss} onChange={this.handleChange('stop_loss')}/>
                          <label className="form-check-label" htmlFor="stop_loss">Stop Loss</label>
                  </div>
                  {this.state.stop_loss && <div className="form-group">
                      <label htmlFor="stop_price">STOP_PRICE</label>
                      <input className="form-control" id="stop_price" name="stop_price" value={this.state.stop_price} onChange={this.handleChange('stop_price')}/>
                  </div>}
                  <div className="form-group form-check">
                      <input type="checkbox" className="form-check-input" id="trailing_stop" value={this.state.trailing_stop} onChange={this.handleChange('trailing_stop')}/>
                          <label className="form-check-label" htmlFor="trailing_stop">Trailing Stop</label>
                  </div>
                  <div className="form-group form-check">
                      <input type="checkbox" className="form-check-input" id="take_profit" value={this.state.take_profit} onChange={this.handleChange('take_profit')}/>
                          <label className="form-check-label" htmlFor="take_profit">Take Profit</label>
                  </div>
                  <div className="form-group form-check">
                      <input type="checkbox" className="form-check-input" id="rebuy_targets" value={this.state.rebuy_targets} onChange={this.handleChange('rebuy_targets')}/>
                          <label className="form-check-label" htmlFor="rebuy_targets">Rebuy Targets</label>
                  </div>
                  <div className="form-group form-check">
                      <input type="checkbox" className="form-check-input" id="condition" value={this.state.condition} onChange={this.handleChange('condition')}/>
                      <label className="form-check-label" htmlFor="condition">Condition</label>
                  </div>
                  {this.state.condition &&
                  <div className="form-group">
                      <select className="form-control" id="condition_type" name="condition_type" value={this.state.condition_type} onChange={this.handleChange('condition_type')}>
                          <option>SELECT CONDITION</option>
                          <option value="GREATER_THAN">GREATER THAN</option>
                          <option value="LESS_THAN">LESS THAN</option>
                          <option value="STOP_LOSS_FIXED">STOP LOSS FIXED</option>
                          <option value="STOP_LOSS_PERCENTAGE">STOP LOSS PERCENTAGE</option>
                      </select>
                  </div>
                  }
                  {
                      this.state.condition_type === "STOP_LOSS_FIXED" &&
                      <div className="form-group">
                          <label htmlFor="target_price">TARGET PRICE</label>
                          <input className="form-control" id="target_price" name="target" value={this.state.target} onChange={this.handleChange('target')}/>
                      </div>
                  }
                  {
                      this.state.condition_type === "STOP_LOSS_PERCENTAGE" &&
                      <div className="form-group">
                          <label htmlFor="target_percentage">TARGET PERCENTAGE</label>
                          <input className="form-control" id="target_percentage" name="target" value={this.state.target} onChange={this.handleChange('target')}/>
                      </div>
                  }
                  <div className="form-group">
                      <label htmlFor="target_percentage">TIME IN EFFECT</label>
                      <select className="form-control" id="time_in_effect" name="time_in_effect" value={this.state.time_in_effect} onChange={this.handleChange('time_in_effect')}>
                          <option value="GOOD_TIL_CANCELLED">GOOD_TIL_CANCELLED</option>
                          <option value="IMMEDIATE_OR_CANCEL">IMMEDIATE_OR_CANCEL</option>
                          <option value="FILL_OR_KILL">FILL_OR_KILL</option>
                      </select>
                  </div>
                  <button type="submit" className="btn btn-primary">Submit</button>
              </form>
          </div>
      );
  }
}

const domContainer = document.querySelector('#bittrex_form');
ReactDOM.render(<BittrexForm/>, domContainer);