import React, {Component} from 'react';
import { connect } from "react-redux";
import {userActions} from "../../actions";
import { Link } from 'react-router-dom';
import {AuthWrapper} from "./wrapper";
import {Spinner} from "../sub-components/spinner";

export class Register extends Component {

    constructor(props) {
        super(props);

        this.state = {
            user: {
                username:'',
                email: '',
                password: '',
                tg_address:''
            },
            submitted: false
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleSocialLogin = this.handleSocialLogin.bind(this);
    }

    handleChange(event) {
        const { name, value } = event.target;
        const { user } = this.state;
        this.setState({
            user: {
                ...user,
                [name]: value
            }
        });
    }

    handleSocialLogin(data) {
        const { type, email, social_id, avatar, username } = data;
        const { dispatch } = this.props;
        dispatch(userActions.oauthlogin({type, email, social_id, avatar_url : avatar, username}))
    }

    handleSubmit(event) {
        event.preventDefault();

        this.setState({ submitted: true });
        const { user } = this.state;
        const { dispatch } = this.props;
        if (user.username && user.email && user.password) {
            dispatch(userActions.register(user));
        }
    }

    render(){

        const { logginIn  } = this.props;
        const { user, submitted } = this.state;

        return (
            <AuthWrapper>
                <div class="login-wrap">
                    <div class="login-content">
                        <div class="login-logo">
                            <a href="#">
                                <img src="images/icon/clown.png" alt="CoolAdmin"/>
                            </a>
                        </div>
                        <div class="login-form">
                            <form onSubmit={this.handleSubmit}>
                                <div class="form-group">
                                    <label>Username</label>
                                    <input type="text" className="au-input au-input--full" name="username" value={user.username} onChange={this.handleChange} />
                                    {submitted && !user.username &&
                                    <div className="help-block">Username is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Email Address</label>
                                    <input type="email" className="au-input au-input--full" name="email" value={user.email} onChange={this.handleChange} />
                                    {submitted && !user.email &&
                                    <div className="help-block">Email is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Password</label>
                                    <input type="password" className="au-input au-input--full" name="password" value={user.password} onChange={this.handleChange} />
                                    {submitted && !user.password &&
                                    <div className="help-block">Password is required</div>
                                    }
                                </div>
                                <div class="form-group">
                                    <label>Confirm Password</label>
                                    <input type="password" className="au-input au-input--full" name="password_confirm" value={user.password_confirm} onChange={this.handleChange} />
                                    {submitted && !user.password_confirm && user.password !== user.password_confirm &&
                                    <div className="help-block">Password Confirmation is required</div>
                                    }
                                </div>
                                <div class="login-checkbox">
                                    <label>
                                        <input type="checkbox" name="aggree"/>Agree the terms and policy
                                    </label>
                                </div>
                                <button class="au-btn au-btn--block au-btn--green m-b-20" type="submit"><Spinner loading={logginIn}/> register</button>
                            </form>
                            <div class="register-link">
                                <p>
                                    Already have account?
                                    <Link to="/login">Sign In</Link>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </AuthWrapper>
        );
    }
}

function mapStateToProps(state) {
    const { logginIn } = state.authentication;
    return {
        logginIn
    };
}

const connectedRegisterPage = connect(mapStateToProps)(Register);
export { connectedRegisterPage as RegisterPage };