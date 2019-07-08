import React,{Component} from 'react';
import Moment from 'react-moment';
import 'moment-timezone';
import Pagination from "react-js-pagination";

class IndexTradesTable extends Component{
    constructor(props){
        super(props);
        this.state = {
            pageNumber:1,
            account: "all",
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange = name => (e) => {
        e.preventDefault();
        const pageCount = parseInt(this.props.trades.length / this.props.itemsCountPerPage) + 1;
        if(name === 'P'){
            if(this.state.pageNumber > 1){
                this.setState({pageNumber: this.state.pageNumber - 1});
            }
        }
        else if(name === 'N'){
            if(this.state.pageNumber < pageCount){
                this.setState({pageNumber: this.state.pageNumber + 1});
            }
        }
        else if(!isNaN(parseInt(name))){
            const pageNumber = parseInt(name);
            if(pageNumber > 0 && pageNumber <= pageCount){
                this.setState({pageNumber: pageNumber});
            }
        }
        else if(name === 'all' || name === 'binance' || name === 'bittrex'){
            this.setState({account: name});
        }
        else{
            alert('finisher');
        }
    }

    render(){
        const {trades} = this.props;
        console.log("Trades are", trades);
        const {account} = this.state;
        const filtered_trades = account !== 'all' ? trades.filter(trade => trade.exchange === account.toUpperCase()): trades;
        const start = (this.state.pageNumber - 1)*this.props.itemsCountPerPage;
        const end = this.state.pageNumber * this.props.itemsCountPerPage;
        const pageCount = parseInt(filtered_trades.length / this.props.itemsCountPerPage) + 1;
        const show_trades = filtered_trades.slice(start, end);
        return <div>
            <div class="row m-t-30">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h4>{account[0].toUpperCase() + account.slice(1)} Trades</h4>
                        </div>
                        <div class="card-body">
                            <div class="custom-tab">
                                <nav>
                                    <div class="nav nav-tabs" id="nav-tab" role="tablist">
                                        <a class="nav-item nav-link active" id="custom-nav-all-tab" onClick={this.handleChange('all')} data-toggle="tab" href="#custom-nav-all" role="tab" aria-controls="custom-nav-all"
                                           aria-selected="true">All</a>
                                        <a class="nav-item nav-link" id="custom-nav-binance-tab" onClick={this.handleChange('binance')} data-toggle="tab" href="#custom-nav-binance" role="tab" aria-controls="custom-nav-binance"
                                           aria-selected="false">Binance</a>
                                        <a class="nav-item nav-link" id="custom-nav-bittrex-tab" onClick={this.handleChange('bittrex')} data-toggle="tab" href="#custom-nav-bittrex" role="tab" aria-controls="custom-nav-bittrex"
                                           aria-selected="false">Bittrex</a>
                                    </div>
                                </nav>
                                <div class="tab-content pl-3 pt-2" id="nav-tabContent">
                                    <div class="table-responsive m-b-40">
                                        <table class="table table-borderless table-data3">
                                            <thead>
                                            <tr>
                                                <th>NO</th>
                                                <th>SIGNAL</th>
                                                <th>SYMBOL</th>
                                                <th>BUY AT</th>
                                                <th>SELL AT</th>
                                                <th>QTY</th>
                                                <th>PNL</th>
                                                <th>STATUS</th>
                                                <th>TIME</th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                            {
                                                show_trades.map((trade, index) => {
                                                    return <tr>
                                                        <td>{trade.id}</td>
                                                        <td>{trade.signal}</td>
                                                        <td>{trade.symbol}</td>
                                                        <td>{trade.buy_price}</td>
                                                        <td>{trade.sell_price}</td>
                                                        <td>{trade.buy_quantity}</td>
                                                        <td>{trade.PNL}</td>
                                                        <td class={trade.sell_status === "FILLED" ? "process" : "denied"}>{
                                                            trade.sell_status === "FILLED" ? "COMPLETE" : "ONGOING"
                                                        }</td>
                                                        <td><Moment fromNowDuring={1000*60*60*24} format="DD-MM-YY,HH:mm">{trade.timestamp}</Moment></td>
                                                    </tr>
                                                })
                                            }
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="user-data__footer">
                        <nav aria-label="Page navigation">
                            <ul class="pagination justify-content-center">
                                <li class="page-item">
                                    <a class="page-link" href="#" aria-label="Previous" onClick={this.handleChange('P')} name='P'>
                                        <span aria-hidden="true">&laquo;</span>
                                        <span class="sr-only">Previous</span>
                                    </a>
                                </li>
                                <li class="page-item"><a class="page-link" href="#" onClick={this.handleChange(1)} name={1}>1</a></li>
                                {
                                    this.state.pageNumber !== 1 && this.state.pageNumber !== pageCount &&
                                    <li class="page-item disabled"><a class="page-link" href="#">{this.state.pageNumber}</a></li>
                                }
                                <li class="page-item"><a class="page-link" href="#" onClick={this.handleChange(pageCount)} name={pageCount}>{pageCount}</a></li>
                                <li class="page-item">
                                    <a class="page-link" href="#" aria-label="Next" onClick={this.handleChange('N')} name='N'>
                                        <span aria-hidden="true">&raquo;</span>
                                        <span class="sr-only">Next</span>
                                    </a>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    }
}

export {IndexTradesTable};