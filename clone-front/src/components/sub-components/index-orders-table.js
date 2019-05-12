import React,{Component} from 'react';
import Moment from 'react-moment';
import 'moment-timezone';
import Pagination from "react-js-pagination";

class IndexOrdersTable extends Component{
    constructor(props){
        super(props);
        this.state = {
            pageNumber:1,
            account: "ALL",
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange = name => (e) => {
        e.preventDefault();
        const pageCount = parseInt(this.props.orders.length / this.props.itemsCountPerPage) + 1;
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
        else if(typeof parseInt(name) === 'number'){
            const pageNumber = parseInt(name);
            if(pageNumber > 0 && pageNumber <= pageCount){
                this.setState({pageNumber: pageNumber});
            }
        }

    }

    render(){

        const {orders} = this.props;
        const start = (this.state.pageNumber - 1)*this.props.itemsCountPerPage;
        const end = this.state.pageNumber * this.props.itemsCountPerPage;
        const pageCount = parseInt(this.props.orders.length / this.props.itemsCountPerPage) + 1;
        const show_orders = orders.slice(start, end)
        return <div class="row m-t-30">
            <div class="overview-wrap">
                <h2 class="title-1">Orders</h2>
            </div>
            <div class="col-md-12">
                <div class="table-responsive m-b-40">
                    <table class="table table-borderless table-data3">
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>date</th>
                            <th>type</th>
                            <th>Symbol</th>
                            <th>status</th>
                            <th>BTC</th>
                        </tr>
                        </thead>
                        <tbody>
                        {
                            show_orders.map(order => {
                                return <tr>
                                    <td>{order.id}</td>
                                    <td><Moment fromNowDuring={1000*60*60*24}>{order.timestamp}</Moment></td>
                                    <td className={order.side === "BUY" ? "process" : "denied"}>{order.side}</td>
                                    <td>{order.symbol}</td>
                                    <td class={order.status === "FILLED" || order.status === "NEW" ? "process" : "denied"}>{order.status}</td>
                                    <td>{order.price}</td>
                                </tr>
                            })
                        }
                        </tbody>
                    </table>
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

    }
}

export {IndexOrdersTable};