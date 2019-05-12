import React,{Component} from 'react';
import { connect } from "react-redux";
import {userActions} from "../../actions";

class AccountMenu extends Component {
    constructor(props)
    {
        super(props);
        this.state = {
            show_dropdown: false
        }
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e){
        e.preventDefault();
        if (e.target.classList.contains( 'logout-button' )) {
            userActions.logout();
        }
        if (!this.state.show_dropdown){
            document.body.addEventListener('click', this.handleChange);
        }
        else{
            document.body.removeEventListener('click', this.handleChange);
        }
        this.setState({ show_dropdown: !this.state.show_dropdown });
        e.stopPropagation();
    }

    render(){

        const {user} = this.props;

        return (
            <div class="account-wrap">
                <div class={this.state.show_dropdown ? "account-item clearfix js-item-menu show-dropdown" : "account-item clearfix js-item-menu"} onClick={this.handleChange}>
                    <div class="image">
                        <img src="/images/icon/2.png" style={{width:'50%', height: '50%' }} alt={user.username} />
                    </div>
                    <div class="content">
                        <a class="js-acc-btn" href="#" onClick={this.handleChange}>{user.username}</a>
                    </div>
                    {
                        this.state.show_dropdown && <div class="account-dropdown js-dropdown">
                            <div class="info clearfix">
                                <div class="image">
                                    <a href="#">
                                        <img src="/images/icon/2.png" alt={user.username} />
                                    </a>
                                </div>
                                <div class="content">
                                    <h5 class="name">
                                        <a href="#">{user.username}</a>
                                    </h5>
                                    <span class="email">{user.email}</span>
                                </div>
                            </div>
                            <div class="account-dropdown__footer">
                                <a href="#" className="logout-button">
                                    <i class="zmdi zmdi-power"></i>Logout</a>
                            </div>
                        </div>
                    }
                </div>
            </div>
        );
    }
}

function mapStateToProps(state) {
    const { user } = state.authentication;
    return {
        user
    };
}

const Wrapper = connect(mapStateToProps)(AccountMenu);
export { Wrapper as AccountMenu  };